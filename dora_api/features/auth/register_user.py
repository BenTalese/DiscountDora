"""POST /api/auth/register — self-serve account creation.

Strengthened in A1 to:
  - Enforce password rules (min 10 chars, ≥1 letter + ≥1 digit).
  - Validate email format and case-insensitively reject duplicates.
  - Mark new accounts `email_verified=false` and send a verification
    email; first-user-is-admin still applies AND auto-verifies the
    admin so a fresh install without SMTP isn't locked out.
  - Stamp `password_changed_at` for the session-staleness check.
  - Audit + rate limit.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict, Field
from werkzeug.security import generate_password_hash

from dora_api.domain.entities.audit_event import SEVERITY_AUDIT
from dora_api.domain.entities.auth_token import PURPOSE_VERIFY_EMAIL
from dora_api.domain.entities.user import User
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation, ok,
                                                  unprocessable_entity,
                                                  ProblemDetails)
from dora_api.infrastructure.audit import emit as audit_emit
from dora_api.infrastructure.auth_helpers import (
    VERIFY_EMAIL_TTL, build_verify_url, is_valid_email, issue_token,
    normalise_email, rate_limit, rate_limit_remaining_seconds, try_send,
    validate_password,
)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.email_sender import render_template, send_email
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


SESSION_USER_ID_KEY = "user_id"
SESSION_PWD_V_KEY = "pwd_v"  # session-staleness check (see get_me)


@dataclass(frozen=True, slots=True)
class AuthenticatedUserDto:
    """Public-safe projection of a User. Never includes password_hash."""
    user_id: UUID
    username: str
    email: str | None
    is_admin: bool
    send_deals_on_day: int
    deals_email_enabled: bool
    deals_email_compact: bool
    theme: str
    font_family: str
    font_size: str
    onboarding_completed_at: str | None
    last_backup_at: str | None
    email_verified: bool
    # P2-05 — grocery budget. `budget_amount` is None when the user
    # hasn't opted in; a positive number turns on the dashboard / Dora
    # budget surfaces. Period is one of "weekly" / "monthly".
    budget_amount: float | None
    budget_period: str
    # P2-13 — voice opt-ins. Both default False; the SPA reads them on
    # boot to seed the per-page mic / volume toggles.
    voice_input_enabled: bool
    voice_output_enabled: bool
    # C-cross Chunk 2 — per-user money-features opt-in (proposal §2.2).
    # Layered with install `money_enabled` via useMoneyEnabled().
    money_features_enabled: bool
    # C-cross Chunk 3 — per-user nutrition mode. `off` | `simple` |
    # `complex` (complex requires admin-configured nutrition source).
    nutrition_mode: str
    # C-cross Chunk 5 — per-user image-display opt-ins (proposal §2.8).
    # Both default True (visual richness on; users opt out).
    show_recipe_images: bool
    show_stock_images: bool
    # Onboarding C-5.4 — household cooking headcount; None = not set.
    household_headcount: int | None
    # C-9.7 — alerts email digest channel (PROPOSAL_ALERTS §3.5).
    # `alerts_email_cadence` is 'off' | 'daily' | 'weekly'; `alerts_email_
    # day` is the weekly send day (Mon=0 … Sun=6, ignored on daily).
    alerts_email_enabled: bool
    alerts_email_cadence: str
    alerts_email_day: int

    @classmethod
    def from_entity(cls, user: User) -> "AuthenticatedUserDto":
        return AuthenticatedUserDto(
            user_id=user.id,
            username=user.username,
            email=user.email,
            is_admin=bool(user.is_admin),
            send_deals_on_day=user.send_deals_on_day,
            deals_email_enabled=bool(user.deals_email_enabled),
            deals_email_compact=bool(user.deals_email_compact),
            theme=user.theme,
            font_family=user.font_family,
            font_size=user.font_size,
            onboarding_completed_at=(
                user.onboarding_completed_at.isoformat()
                if user.onboarding_completed_at is not None else None
            ),
            last_backup_at=(
                user.last_backup_at.isoformat()
                if user.last_backup_at is not None else None
            ),
            email_verified=bool(user.email_verified),
            budget_amount=(
                float(user.budget_amount) if user.budget_amount is not None else None
            ),
            budget_period=user.budget_period,
            voice_input_enabled=bool(user.voice_input_enabled),
            voice_output_enabled=bool(user.voice_output_enabled),
            money_features_enabled=bool(user.money_features_enabled),
            nutrition_mode=user.nutrition_mode,
            show_recipe_images=bool(user.show_recipe_images),
            show_stock_images=bool(user.show_stock_images),
            household_headcount=(
                int(user.household_headcount)
                if user.household_headcount is not None else None
            ),
            alerts_email_enabled=bool(user.alerts_email_enabled),
            alerts_email_cadence=user.alerts_email_cadence,
            alerts_email_day=int(user.alerts_email_day),
        )


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)


@dataclass(slots=True)
class RegisterUserResponse:
    new_user_id: UUID = EMPTY_UUID
    username_taken: bool = False
    email_taken: bool = False
    is_admin: bool = False
    is_first_user: bool = False
    verify_token: str | None = None
    verify_user_email: str | None = None
    verify_username: str | None = None


class RegisterUserHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: RegisterUserRequest) -> RegisterUserResponse:
        username_field = EntityField(User, User.Fields.USERNAME)
        if self.repository.get(User).one(username_field.eq(request.username)):
            return RegisterUserResponse(username_taken=True)

        email_norm = normalise_email(request.email)
        if email_norm:
            email_field = EntityField(User, User.Fields.EMAIL)
            existing_by_email = self.repository.get(User).one(email_field.eq(email_norm))
            if existing_by_email is not None:
                return RegisterUserResponse(email_taken=True)

        is_first_user = self.repository.get(User).count() == 0
        now = datetime.now(timezone.utc)
        new_user = User(
            email=email_norm,
            password_hash=generate_password_hash(request.password),
            send_deals_on_day=0,
            username=request.username,
            is_admin=is_first_user,
            email_verified=is_first_user,  # sysadmin self-verifies
            password_changed_at=now,
        )
        self.repository.add(new_user)
        self.repository.save_changes()

        verify_token = None
        if email_norm and not is_first_user:
            verify_token = issue_token(
                new_user.id, PURPOSE_VERIFY_EMAIL, VERIFY_EMAIL_TTL,
            )

        return RegisterUserResponse(
            new_user_id=new_user.id,
            is_admin=is_first_user,
            is_first_user=is_first_user,
            verify_token=verify_token,
            verify_user_email=email_norm,
            verify_username=request.username,
        )


@AUTH_ROUTER.route("/register", methods=["POST"])
@has_request_body(RegisterUserRequest)
def register_user():
    _Logger = logging.getLogger(__name__)

    if not rate_limit("auth.register", max_per_minute=10):
        return _too_many_requests(
            rate_limit_remaining_seconds("auth.register", 10),
        )

    request_body: RegisterUserRequest = get_request_body()

    # Surface the validation problems together so the SPA can render a
    # one-shot list of issues instead of nagging field-by-field.
    issues: dict[str, list[str]] = {}
    if request_body.email is not None and not is_valid_email(request_body.email):
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

    handler = get_container().inject(RegisterUserHandler)
    response = handler.handle(request_body)

    if response.username_taken:
        _Logger.warning(f"Registration rejected — username taken: {request_body.username}")
        return business_rule_violation(f"Username '{request_body.username}' is already taken.")
    if response.email_taken:
        _Logger.warning(f"Registration rejected — email taken: {request_body.email}")
        return business_rule_violation("That email address is already registered.")

    # Auto-login the freshly registered user.
    session.clear()
    session[SESSION_USER_ID_KEY] = str(response.new_user_id)
    session[SESSION_PWD_V_KEY] = datetime.now(timezone.utc).isoformat()
    session.permanent = True

    # Fire the verification email (best effort).
    if response.verify_token and response.verify_user_email:
        try_send(
            send_email,
            to=response.verify_user_email,
            subject="Verify your Dashy Dora account",
            html_body=render_template(
                "verify_email.html",
                subject="Verify your Dashy Dora account",
                username=response.verify_username or "there",
                verify_url=build_verify_url(response.verify_token),
            ),
            text_body=(
                f"Hi {response.verify_username}, verify your Dashy Dora "
                f"account: {build_verify_url(response.verify_token)} "
                f"(expires in 24 hours)"
            ),
        )

    audit_emit(
        "auth.user.registered",
        severity=SEVERITY_AUDIT,
        actor_user_id=response.new_user_id,
        entity_type="User", entity_id=response.new_user_id,
        payload={"username": request_body.username, "first_user": response.is_first_user},
    )

    _Logger.info(f"Registered user {request_body.username} ({response.new_user_id})")
    return ok({
        "user_id": str(response.new_user_id),
        "username": request_body.username,
        "email": normalise_email(request_body.email),
        "is_admin": response.is_admin,
        "email_verified": response.is_first_user,
        "verification_sent": bool(response.verify_token),
    })


def _too_many_requests(retry_after: int):
    from flask import jsonify
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
