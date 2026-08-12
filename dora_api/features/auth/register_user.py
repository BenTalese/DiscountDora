"""POST /api/auth/register — self-serve account creation.

Strengthened in A1 to:
  - Enforce password rules (min 10 chars, ≥1 letter + ≥1 digit).
  - Validate email format and case-insensitively reject duplicates.
  - Mark new accounts `email_verified=false` and send a verification
    email.
  - Stamp `password_changed_at` for the session-staleness check.
  - Audit + rate limit.

FU-200: /register no longer grants admin to the first registrant. The
first-admin bootstrap lives at POST /api/auth/bootstrap-admin (a
single-use endpoint that 410s once any user exists). Regular signups
created here are always `is_admin=False` and `email_verified=False`
until they click the verification link.
"""
import dataclasses
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict, Field

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
    VERIFY_EMAIL_TTL, build_verify_url, hash_password, is_valid_email,
    issue_token, normalise_email, rate_limit, rate_limit_remaining_seconds,
    try_send, validate_password,
)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.email_sender import render_template, send_email
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


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
    email_verified: bool
    # grocery budget moved to AppSetting (install-wide household budget);
    # clients read it via /api/health.budget_policy, not this user DTO.
    # voice opt-ins. Both default False; the SPA reads them on
    # boot to seed the per-page mic / volume toggles.
    voice_input_enabled: bool
    voice_output_enabled: bool
    # Voice engine ('browser' | 'piper') + chosen Piper voice id. The SPA
    # reads these on boot to drive useSpeechOutput (which engine + voice to
    # synthesize with, with a browser fallback when Piper is unavailable).
    voice_engine: str
    voice_id: str
    # money opt-in removed — money is a single install-wide flag
    # (AppSetting.money_enabled); there is no per-user money layer.
    # FU-615 — `batch_features_enabled` moved to AppSetting (install-wide);
    # clients read the cook-style via /api/health.cooking_policy.
    # "always ask which draft list on quick-add".
    always_ask_which_shopping_list: bool
    # Zero-Input Pantry opt-out (default True).
    inferred_pantry_enabled: bool
    # C-cross Chunk 3 — per-user nutrition mode. `off` | `simple` |
    # `complex` (complex requires admin-configured nutrition source).
    nutrition_mode: str
    # C-cross Chunk 5 — per-user recipe-image opt-in (proposal §2.8).
    # Default True. FU-508 dropped the stock-image companion.
    show_recipe_images: bool
    # FU-615 — `household_headcount` moved to AppSetting (install-wide);
    # clients read it via /api/health.cooking_policy.
    # alerts email digest channel (PROPOSAL_ALERTS §3.5).
    # `alerts_email_cadence` is 'off' | 'daily' | 'weekly'; `alerts_email_
    # day` is the weekly send day (Mon=0 … Sun=6, ignored on daily).
    alerts_email_enabled: bool
    alerts_email_cadence: str
    alerts_email_day: int
    # Settings rebuild Phase 4 (§2.9) — whether the user has a profile
    # picture. Bytes never travel inline; the SPA fetches them via
    # `GET /users/<id>/image`. For this single-user projection it's a cheap
    # `is not None` check (the deferred blob loads once); the user-list DTO
    # bulk-stamps it instead (get_users) to avoid per-row byte loads.
    has_image: bool
    # Dashboard rebuild Phase 2 — per-user dashboard layout JSON (card order +
    # hidden set), or None when the user hasn't customised. The SPA parses it
    # to seed the dashboard; the backend treats it as an opaque string.
    dashboard_layout: str | None
    # per-user assistant config. Plaintext API key
    # is never echoed back — the wire-side carries a derived
    # `has_llm_api_key: bool` (same shape as `has_image`). The other
    # four fields round-trip directly so the Settings page can show /
    # edit them; the actual provider client is built server-side per
    # request (factory.build_assistant_client).
    llm_enabled: bool
    llm_provider: str | None
    llm_base_url: str | None
    llm_model: str | None
    has_llm_api_key: bool
    # FU-360.6 — whether to mount the Dora helper bubble at all. Default
    # True; distinct from `llm_enabled` (AI mode). When False the SPA hides
    # the launcher entirely.
    show_assistant: bool

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
            email_verified=bool(user.email_verified),
            voice_input_enabled=bool(user.voice_input_enabled),
            voice_output_enabled=bool(user.voice_output_enabled),
            voice_engine=user.voice_engine,
            voice_id=user.voice_id,
            always_ask_which_shopping_list=bool(user.always_ask_which_shopping_list),
            inferred_pantry_enabled=bool(user.inferred_pantry_enabled),
            nutrition_mode=user.nutrition_mode,
            show_recipe_images=bool(user.show_recipe_images),
            alerts_email_enabled=bool(user.alerts_email_enabled),
            alerts_email_cadence=user.alerts_email_cadence,
            alerts_email_day=int(user.alerts_email_day),
            has_image=user.image is not None,
            dashboard_layout=user.dashboard_layout,
            llm_enabled=bool(user.llm_enabled),
            llm_provider=user.llm_provider,
            llm_base_url=user.llm_base_url,
            llm_model=user.llm_model,
            has_llm_api_key=user.llm_api_key_encrypted is not None,
            show_assistant=bool(user.show_assistant),
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
    # bootstrap_required is True when there's no admin yet — the
    # SPA shouldn't even reach /register in that case; we return a 409 at
    # the handler level so a direct API caller is told to use the
    # bootstrap endpoint instead.
    bootstrap_required: bool = False
    verify_token: str | None = None
    verify_user_email: str | None = None
    verify_username: str | None = None


class RegisterUserHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: RegisterUserRequest) -> RegisterUserResponse:
        # refuse self-serve registration until an admin exists.
        # The fresh-install surface is /bootstrap-admin (single-use),
        # not /register.
        if self.repository.get(User).count() == 0:
            return RegisterUserResponse(bootstrap_required=True)

        username_field = EntityField(User, User.Fields.USERNAME)
        if self.repository.get(User).one(username_field.eq(request.username)):
            return RegisterUserResponse(username_taken=True)

        email_norm = normalise_email(request.email)
        if email_norm:
            email_field = EntityField(User, User.Fields.EMAIL)
            existing_by_email = self.repository.get(User).one(email_field.eq(email_norm))
            if existing_by_email is not None:
                return RegisterUserResponse(email_taken=True)

        now = datetime.now(timezone.utc)
        new_user = User(
            email=email_norm,
            password_hash=hash_password(request.password),
            send_deals_on_day=0,
            username=request.username,
            # /register never grants admin. The bootstrap endpoint
            # owns that path, and admin promotion otherwise goes through
            # the Users admin page.
            is_admin=False,
            email_verified=False,
            password_changed_at=now,
        )
        self.repository.add(new_user)
        self.repository.save_changes()

        verify_token = None
        if email_norm:
            verify_token = issue_token(
                new_user.id, PURPOSE_VERIFY_EMAIL, VERIFY_EMAIL_TTL,
            )

        return RegisterUserResponse(
            new_user_id=new_user.id,
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

    handler = RegisterUserHandler(SqlAlchemyRepository())
    response = handler.handle(request_body)

    if response.bootstrap_required:
        # empty DB → /register is closed. Force the caller through
        # /bootstrap-admin instead. 409 (Conflict) signals "the system is
        # in a state that disallows this request"; the SPA's router guard
        # already redirects to /setup, so this branch is only reachable
        # via direct API calls.
        _Logger.warning(
            "Registration rejected — no admin exists yet; "
            "/bootstrap-admin is the correct endpoint"
        )
        from flask import jsonify
        from http.client import CONFLICT
        body = jsonify(ProblemDetails(
            detail=(
                "This installation has no admin account yet. "
                "POST to /api/auth/bootstrap-admin to create the first "
                "admin."
            ),
            errors={}, status=CONFLICT,
            title="Setup required.",
            type="https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.8",
        ))
        body.content_type = "application/problem+json"
        body.status_code = CONFLICT
        return body
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
        payload={"username": request_body.username},
    )

    _Logger.info(f"Registered user {request_body.username} ({response.new_user_id})")
    # return the full AuthenticatedUserDto so the SPA can hydrate
    # the auth store from a single call (parity with /login and /me). The
    # old ad-hoc dict had drifted: `has_image` and `dashboard_layout` were
    # missing, and a stale `verification_sent` flag rode alongside. Keep
    # the verification flag as an extra alongside the DTO so the SPA can
    # decide whether to surface a "check your email" toast.
    new_user = SqlAlchemyRepository().get(User).by_id(response.new_user_id)
    body = dataclasses.asdict(AuthenticatedUserDto.from_entity(new_user))
    body["user_id"] = str(body["user_id"])
    body["verification_sent"] = bool(response.verify_token)
    return ok(body)


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
