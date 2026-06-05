"""All the out-of-band auth flows in one file so the shared imports +
rate-limit/scrub boilerplate doesn't get duplicated six times.

Endpoints:
  POST /api/auth/verify-email           — body {token}
  POST /api/auth/resend-verification    — body {email}; anti-enumeration
  POST /api/auth/forgot-password        — body {email}; anti-enumeration
  POST /api/auth/reset-password         — body {token, new_password}
  POST /api/auth/me/email               — auth'd; body {new_email}
  POST /api/auth/email-change/confirm   — body {token}; consumes the
                                          change_email token + swaps the
                                          stored address.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from flask import jsonify, session
from pydantic import BaseModel, ConfigDict, Field
from werkzeug.security import generate_password_hash

from dora_api.domain.entities.audit_event import SEVERITY_AUDIT, SEVERITY_WARN
from dora_api.domain.entities.auth_token import (
    PURPOSE_CHANGE_EMAIL, PURPOSE_RESET_PASSWORD, PURPOSE_VERIFY_EMAIL,
)
from dora_api.domain.entities.user import User
from dora_api.features.auth.register_user import (
    SESSION_PWD_V_KEY, SESSION_USER_ID_KEY,
)
from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import (
    bad_request, no_content, ok, ProblemDetails, unauthorized,
    unprocessable_entity,
)
from dora_api.infrastructure.audit import emit as audit_emit
from dora_api.infrastructure.auth_helpers import (
    CHANGE_EMAIL_TTL, RESET_PASSWORD_TTL, VERIFY_EMAIL_TTL,
    build_reset_url, build_verify_url, consume_token, find_active_token,
    is_valid_email, issue_token, normalise_email, rate_limit,
    rate_limit_remaining_seconds, revoke_tokens_for_user, try_send,
    validate_password,
)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.email_sender import render_template, send_email
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_Logger = logging.getLogger(__name__)


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


def _validation_failure(errors: dict):
    return unprocessable_entity(ProblemDetails(
        detail="See errors property for more details.",
        errors=errors, status=422, title="Validation failed.",
        type="https://datatracker.ietf.org/doc/html/rfc4918#section-11.2",
    ))


# ── /verify-email ──────────────────────────────────────────────────────

class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1, max_length=255)


@AUTH_ROUTER.route("/verify-email", methods=["POST"])
@has_request_body(VerifyEmailRequest)
def verify_email():
    body: VerifyEmailRequest = get_request_body()
    if not rate_limit("auth.verify_email", max_per_minute=10):
        return _too_many_requests(rate_limit_remaining_seconds("auth.verify_email", 10))

    token_row = find_active_token(body.token, PURPOSE_VERIFY_EMAIL)
    if token_row is None:
        return bad_request("This verification link is invalid or expired.")
    repo = SqlAlchemyRepository()
    user = repo.get(User).by_id(token_row.user_id)
    if user is None:
        return bad_request("This verification link is invalid or expired.")

    user.email_verified = True
    repo.save_changes()
    consume_token(token_row.id)

    audit_emit(
        "auth.email.verified",
        severity=SEVERITY_AUDIT,
        actor_user_id=user.id,
        entity_type="User", entity_id=user.id,
    )
    _Logger.info("Email verified for user %s", user.id)
    return ok({"email_verified": True})


# ── /resend-verification ───────────────────────────────────────────────

class ResendVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=1, max_length=255)


@AUTH_ROUTER.route("/resend-verification", methods=["POST"])
@has_request_body(ResendVerificationRequest)
def resend_verification():
    body: ResendVerificationRequest = get_request_body()
    # Brief: "1/min per IP + email". One bucket per email-on-this-IP combo.
    if not rate_limit(f"auth.resend.{normalise_email(body.email)}", max_per_minute=1):
        # Stay anti-enumeration even when rate-limited.
        return no_content()

    email_norm = normalise_email(body.email)
    if not email_norm or not is_valid_email(email_norm):
        return no_content()  # Don't leak that the address is malformed.

    repo = SqlAlchemyRepository()
    user = repo.get(User).one(EntityField(User, User.Fields.EMAIL).eq(email_norm))
    if user is not None and not user.email_verified:
        raw = issue_token(user.id, PURPOSE_VERIFY_EMAIL, VERIFY_EMAIL_TTL)
        try_send(
            send_email,
            to=email_norm,
            subject="Verify your Dashy Dora account",
            html_body=render_template(
                "verify_email.html",
                subject="Verify your Dashy Dora account",
                username=user.username,
                verify_url=build_verify_url(raw),
            ),
            text_body=f"Verify: {build_verify_url(raw)} (expires in 24h)",
        )

    # Always 204 — same response regardless of whether the email exists,
    # is verified, or not.
    return no_content()


# ── /forgot-password ───────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=1, max_length=255)


@AUTH_ROUTER.route("/forgot-password", methods=["POST"])
@has_request_body(ForgotPasswordRequest)
def forgot_password():
    body: ForgotPasswordRequest = get_request_body()
    if not rate_limit(f"auth.forgot.{normalise_email(body.email)}", max_per_minute=5):
        return no_content()

    email_norm = normalise_email(body.email)
    if not email_norm or not is_valid_email(email_norm):
        return no_content()

    repo = SqlAlchemyRepository()
    user = repo.get(User).one(EntityField(User, User.Fields.EMAIL).eq(email_norm))
    if user is not None:
        raw = issue_token(user.id, PURPOSE_RESET_PASSWORD, RESET_PASSWORD_TTL)
        try_send(
            send_email,
            to=email_norm,
            subject="Reset your Dashy Dora password",
            html_body=render_template(
                "reset_password.html",
                subject="Reset your Dashy Dora password",
                username=user.username,
                reset_url=build_reset_url(raw),
            ),
            text_body=f"Reset: {build_reset_url(raw)} (expires in 1h, single-use)",
        )
        audit_emit(
            "auth.password.reset_requested",
            severity=SEVERITY_AUDIT,
            actor_user_id=user.id,
            entity_type="User", entity_id=user.id,
        )
    return no_content()


# ── /reset-password ────────────────────────────────────────────────────

class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=1, max_length=255)


@AUTH_ROUTER.route("/reset-password", methods=["POST"])
@has_request_body(ResetPasswordRequest)
def reset_password():
    body: ResetPasswordRequest = get_request_body()
    if not rate_limit("auth.reset_password", max_per_minute=5):
        return _too_many_requests(rate_limit_remaining_seconds("auth.reset_password", 5))

    pwd_error = validate_password(body.new_password)
    if pwd_error:
        return _validation_failure({"new_password": [pwd_error]})

    token_row = find_active_token(body.token, PURPOSE_RESET_PASSWORD)
    if token_row is None:
        return bad_request("This reset link is invalid or expired.")
    repo = SqlAlchemyRepository()
    user = repo.get(User).by_id(token_row.user_id)
    if user is None:
        return bad_request("This reset link is invalid or expired.")

    user.password_hash = generate_password_hash(body.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    repo.save_changes()
    consume_token(token_row.id)
    # Anyone else holding an unused reset link is now out of luck — that's
    # the intent.
    revoke_tokens_for_user(user.id, PURPOSE_RESET_PASSWORD)

    audit_emit(
        "auth.password.reset",
        severity=SEVERITY_AUDIT,
        actor_user_id=user.id,
        entity_type="User", entity_id=user.id,
    )
    if user.email:
        try_send(
            send_email,
            to=user.email,
            subject="Your Dashy Dora password was reset",
            html_body=render_template(
                "password_changed.html",
                subject="Your Dashy Dora password was reset",
                username=user.username,
            ),
            text_body=f"Hi {user.username}, your Dashy Dora password was just reset.",
        )

    _Logger.info("Password reset for user %s", user.id)
    return ok({"password_reset": True})


# ── /me/email (change-email request) ───────────────────────────────────

class ChangeEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_email: str = Field(min_length=1, max_length=255)


@AUTH_ROUTER.route("/me/email", methods=["POST"])
@has_request_body(ChangeEmailRequest)
def request_email_change():
    raw = session.get(SESSION_USER_ID_KEY)
    if not raw:
        return unauthorized()
    try:
        user_id = UUID(raw)
    except (ValueError, TypeError):
        session.clear()
        return unauthorized()

    body: ChangeEmailRequest = get_request_body()
    new_email = normalise_email(body.new_email)
    if not new_email or not is_valid_email(new_email):
        return _validation_failure({"new_email": ["Please enter a valid email address."]})

    repo = SqlAlchemyRepository()
    user = repo.get(User).by_id(user_id)
    if user is None:
        session.clear()
        return unauthorized()

    # Reject if another user already owns this email.
    other = repo.get(User).one(EntityField(User, User.Fields.EMAIL).eq(new_email))
    if other is not None and other.id != user.id:
        return _validation_failure({"new_email": ["That email is already in use."]})

    raw_token = issue_token(
        user.id, PURPOSE_CHANGE_EMAIL, CHANGE_EMAIL_TTL,
        payload=new_email,
    )
    try_send(
        send_email,
        to=new_email,
        subject="Confirm your new Dashy Dora email",
        html_body=render_template(
            "verify_email.html",
            subject="Confirm your new Dashy Dora email",
            username=user.username,
            verify_url=f"{build_verify_url(raw_token).replace('/verify-email', '/confirm-email-change')}",
        ),
        text_body=f"Confirm: {build_verify_url(raw_token)}",
    )
    return no_content()


class ConfirmEmailChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1, max_length=255)


@AUTH_ROUTER.route("/email-change/confirm", methods=["POST"])
@has_request_body(ConfirmEmailChangeRequest)
def confirm_email_change():
    body: ConfirmEmailChangeRequest = get_request_body()
    token_row = find_active_token(body.token, PURPOSE_CHANGE_EMAIL)
    if token_row is None or not token_row.payload:
        return bad_request("This confirmation link is invalid or expired.")
    repo = SqlAlchemyRepository()
    user = repo.get(User).by_id(token_row.user_id)
    if user is None:
        return bad_request("This confirmation link is invalid or expired.")
    # Re-check uniqueness in case someone else claimed the address in
    # the meantime.
    other = repo.get(User).one(EntityField(User, User.Fields.EMAIL).eq(token_row.payload))
    if other is not None and other.id != user.id:
        return bad_request("That email is already in use.")
    user.email = token_row.payload
    user.email_verified = True
    repo.save_changes()
    consume_token(token_row.id)
    audit_emit(
        "auth.email.changed",
        severity=SEVERITY_AUDIT,
        actor_user_id=user.id,
        entity_type="User", entity_id=user.id,
    )
    return ok({"email": user.email})
