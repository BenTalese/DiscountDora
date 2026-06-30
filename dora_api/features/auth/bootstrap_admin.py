"""POST /api/auth/bootstrap-admin — one-shot first-admin creation.

FU-200 fix. Splits the historical "first POST to /register silently becomes
admin" race out of the public registration handler and into a dedicated
endpoint that:

  - 410 Gone once any User row exists (the endpoint is single-use).
  - Honours ADMIN_BOOTSTRAP_EMAIL when set — only that address (case-
    insensitive) is allowed to bootstrap. Without the env var we fall back
    to "the first POST wins", which is the dev-mode default.
  - Auto-verifies the new admin (no SMTP dependency on a fresh install) and
    auto-logs them in, matching the old register-first-user UX.

A companion GET /api/auth/bootstrap-required tells the SPA whether to
route a fresh visitor to /setup or /login. It exposes a single boolean,
not a user count — never leaks the population size.
"""
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from http.client import GONE

from flask import jsonify, session
from pydantic import BaseModel, ConfigDict, Field
from werkzeug.security import generate_password_hash

from dora_api.domain.entities.audit_event import SEVERITY_AUDIT, SEVERITY_WARN
from dora_api.domain.entities.user import User
from dora_api.features.auth.register_user import (AuthenticatedUserDto,
                                                  SESSION_PWD_V_KEY,
                                                  SESSION_USER_ID_KEY)
from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import (ProblemDetails, ok,
                                                  unprocessable_entity)
from dora_api.infrastructure.audit import emit as audit_emit
from dora_api.infrastructure.auth_helpers import (is_valid_email,
                                                  normalise_email,
                                                  rate_limit,
                                                  rate_limit_remaining_seconds,
                                                  validate_password)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class BootstrapAdminRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    # Email is required for the admin account so password-reset works on a
    # fresh install. Public /register still keeps email optional.
    email: str = Field(min_length=1, max_length=255)


def _gone(detail: str):
    response = jsonify(ProblemDetails(
        detail=detail, errors={}, status=GONE,
        title="Setup already complete.",
        type="https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.9",
    ))
    response.content_type = "application/problem+json"
    response.status_code = GONE
    return response


def _too_many_requests(retry_after: int):
    from http.client import TOO_MANY_REQUESTS
    response = jsonify(ProblemDetails(
        detail=f"Too many requests. Try again in {retry_after}s.",
        errors={}, status=TOO_MANY_REQUESTS, title="Rate limit exceeded.",
        type="https://datatracker.ietf.org/doc/html/rfc6585#section-4",
    ))
    response.content_type = "application/problem+json"
    response.status_code = TOO_MANY_REQUESTS
    response.headers["Retry-After"] = str(max(retry_after, 1))
    return response


def _user_count() -> int:
    return SqlAlchemyRepository().get(User).count()


def _bootstrap_email_required() -> str | None:
    """The configured ADMIN_BOOTSTRAP_EMAIL (case-folded). None when unset
    or blank — caller falls back to "first POST wins" behaviour."""
    raw = (os.environ.get("ADMIN_BOOTSTRAP_EMAIL") or "").strip()
    return raw.lower() if raw else None


@AUTH_ROUTER.route("/bootstrap-required", methods=["GET"])
def bootstrap_required():
    return ok({"required": _user_count() == 0})


@AUTH_ROUTER.route("/bootstrap-admin", methods=["POST"])
@has_request_body(BootstrapAdminRequest)
def bootstrap_admin():
    _Logger = logging.getLogger(__name__)

    if not rate_limit("auth.bootstrap", max_per_minute=5):
        return _too_many_requests(
            rate_limit_remaining_seconds("auth.bootstrap", 5),
        )

    # Closed once any user exists. Checked twice — here (cheap fast-reject
    # for the common "someone refreshed the tab" case) and again inside
    # the transaction below (the actual race-safety guard).
    if _user_count() != 0:
        return _gone(
            "An admin account already exists. Sign in instead."
        )

    request_body: BootstrapAdminRequest = get_request_body()

    issues: dict[str, list[str]] = {}
    if not is_valid_email(request_body.email):
        issues["email"] = ["Please enter a valid email address."]
    pwd_error = validate_password(request_body.password)
    if pwd_error:
        issues["password"] = [pwd_error]
    if issues:
        return unprocessable_entity(ProblemDetails(
            detail="See errors property for more details.",
            errors=issues, status=422, title="Validation failed.",
            type="https://datatracker.ietf.org/doc/html/rfc4918#section-11.2",
        ))

    email_norm = normalise_email(request_body.email)
    required_email = _bootstrap_email_required()
    if required_email is not None and (email_norm or "").lower() != required_email:
        # Don't leak the configured admin email — generic refusal. The
        # operator deploying with ADMIN_BOOTSTRAP_EMAIL set knows what
        # they configured; a drive-by attacker doesn't.
        audit_emit(
            "auth.bootstrap.rejected",
            severity=SEVERITY_WARN,
            payload={"reason": "email_mismatch"},
        )
        _Logger.warning(
            "bootstrap-admin rejected: submitted email does not match "
            "ADMIN_BOOTSTRAP_EMAIL"
        )
        return _gone(
            "This installation is locked to a pre-configured admin "
            "email. Contact the operator."
        )

    repo = SqlAlchemyRepository()
    # Re-check inside the same transaction. The session here owns the
    # connection until save_changes() commits, so a concurrent POST that
    # also reaches this point will land on a unique-constraint failure
    # (username/email) or end up serialised behind us — either way only
    # one POST creates an admin.
    if repo.get(User).count() != 0:
        return _gone(
            "An admin account already exists. Sign in instead."
        )

    from dora_api.persistence.field import EntityField
    username_field = EntityField(User, User.Fields.USERNAME)
    if repo.get(User).one(username_field.eq(request_body.username)):
        return unprocessable_entity(ProblemDetails(
            detail="See errors property for more details.",
            errors={"username": [
                f"Username '{request_body.username}' is already taken."
            ]},
            status=422, title="Validation failed.",
            type="https://datatracker.ietf.org/doc/html/rfc4918#section-11.2",
        ))

    now = datetime.now(timezone.utc)
    new_user = User(
        email=email_norm,
        password_hash=generate_password_hash(request_body.password),
        send_deals_on_day=0,
        username=request_body.username,
        is_admin=True,
        email_verified=True,  # bootstrap admin self-verifies (no SMTP needed)
        password_changed_at=now,
    )
    repo.add(new_user)
    repo.save_changes()

    # Auto-login the new admin so they don't have to bounce through /login
    # after setup.
    session.clear()
    session[SESSION_USER_ID_KEY] = str(new_user.id)
    session[SESSION_PWD_V_KEY] = now.isoformat()
    session.permanent = True

    audit_emit(
        "auth.bootstrap.admin_created",
        severity=SEVERITY_AUDIT,
        actor_user_id=new_user.id,
        entity_type="User", entity_id=new_user.id,
        payload={"username": new_user.username},
    )
    _Logger.info(
        f"Bootstrapped first admin {new_user.username} ({new_user.id})"
    )

    import dataclasses
    body = dataclasses.asdict(AuthenticatedUserDto.from_entity(new_user))
    body["user_id"] = str(body["user_id"])
    return ok(body)
