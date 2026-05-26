import logging
import time
from http.client import NOT_FOUND
from uuid import uuid4

from flask import Blueprint, g, jsonify, request, session
from pydantic import ValidationError

from dora_api.infrastructure.api_response import (ProblemDetails, bad_request,
                                                  unauthorized)
from dora_api.infrastructure.audit import auto_audit_after_request
from dora_api.infrastructure.decorators import REQUEST_BODYS_BY_ENDPOINT
from dora_api.infrastructure.log_context import (reset_context, set_request_id,
                                                 set_user_id)


_Logger = logging.getLogger(__name__)
MIDDLEWARE = Blueprint('MIDDLEWARE', __name__)


# Endpoints that don't require an authenticated session. Anything under /api/
# that isn't listed here is gated by the require_auth hook below.
PUBLIC_ENDPOINTS = frozenset({
    "login",
    "register_user",
    "health_check",            # health probes must not require auth (used by container orchestrators)
    "submit_client_log",       # the SPA may need to ship errors before login completes
    # ── A1 out-of-band auth flows; reached from email links + login screen ──
    "verify_email",
    "resend_verification",
    "forgot_password",
    "reset_password",
    "confirm_email_change",
})


@MIDDLEWARE.before_app_request
def handle_incoming_request():
    # ── Logging context ──────────────────────────────────────────────
    # X-Request-Id from the caller is honoured (round-trips across our
    # axios client, which generates one per call) so client + server
    # log lines correlate. Falls back to a fresh uuid4 for ad-hoc curls.
    incoming = request.headers.get("X-Request-Id")
    request_id = incoming.strip() if incoming else uuid4().hex
    set_request_id(request_id)
    set_user_id(session.get("user_id"))
    g.request_started_at = time.perf_counter()
    g.request_id = request_id

    if _Logger.isEnabledFor(logging.INFO):
        _Logger.info(
            "→ %s %s",
            request.method,
            request.path,
        )
    if _Logger.isEnabledFor(logging.DEBUG):
        audit_incoming_request()

    # CORS preflights are anonymous by design — flask-cors handles them and
    # adds the appropriate Access-Control-* headers on the response. Let the
    # request through without auth-gating or body parsing.
    if request.method.upper() == "OPTIONS":
        return

    if not request.endpoint:
        return jsonify(ProblemDetails(
            detail = "Endpoint was not found.",
            status = NOT_FOUND,
            errors = {},
            title = "Endpoint was not found.",
            type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4")), 404

    # Auth gate runs before body deserialisation so unauthenticated callers
    # don't waste cycles having their payloads parsed.
    _AuthFailure = require_auth_if_protected(request.endpoint.split(".")[-1])
    if _AuthFailure is not None:
        return _AuthFailure

    if request.method.upper() in ["POST", "PATCH", "PUT"]:
        return deserialise_web_request(request.endpoint.split(".")[-1])

    return


@MIDDLEWARE.after_app_request
def emit_audit_event(response):
    """Best-effort audit emit for mutating routes. Runs before
    `stamp_request_id` so the audit row already has `request_id` from
    contextvars. Never raises."""
    return auto_audit_after_request(response)


@MIDDLEWARE.after_app_request
def stamp_request_id(response):
    """Echo X-Request-Id on every response so the SPA can correlate its
    own log lines with the server's, and log the request-end summary."""
    started = getattr(g, "request_started_at", None)
    request_id = getattr(g, "request_id", None)
    if request_id:
        response.headers["X-Request-Id"] = request_id
    if started is not None and _Logger.isEnabledFor(logging.INFO):
        duration_ms = (time.perf_counter() - started) * 1000.0
        _Logger.info(
            "← %d %s %s (%.1fms)",
            response.status_code,
            request.method,
            request.path,
            duration_ms,
        )
    return response


@MIDDLEWARE.teardown_app_request
def clear_context(_exc):
    # Reset contextvars so APScheduler / cleanup logs after the request
    # don't get tagged with the previous user's id.
    reset_context()


def require_auth_if_protected(endpoint_name: str):
    """Return an unauthorized response if the endpoint requires a session and
    the caller doesn't have one. Returns None when the request may proceed.
    """
    if not request.path.startswith("/api/"):
        return None
    if endpoint_name in PUBLIC_ENDPOINTS:
        return None
    if "user_id" in session:
        return None
    return unauthorized()


def audit_incoming_request():
    _Logger.debug(
        "Incoming request | method=%s path=%s endpoint=%s ip=%s",
        request.method,
        request.path,
        request.endpoint,
        request.remote_addr,
    )
    _Logger.debug(
        f"body: {request.get_json(silent=True)}" if request.is_json else ""
    )


def deserialise_web_request(request_endpoint: str):
    # Endpoints without a registered schema accept no body (e.g. action POSTs).
    if request_endpoint not in REQUEST_BODYS_BY_ENDPOINT:
        return

    _RequestBodySchema = REQUEST_BODYS_BY_ENDPOINT[request_endpoint]
    try:
        _Parsed = _RequestBodySchema.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        _Errors = {
            ".".join(str(loc) for loc in err["loc"]): [err["msg"]]
            for err in e.errors()
        }
        return bad_request("Malformed request.", errors = _Errors)

    setattr(request, "request_body", _Parsed)
