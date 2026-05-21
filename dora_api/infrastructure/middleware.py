import logging
from http.client import NOT_FOUND

from flask import Blueprint, jsonify, request, session
from pydantic import ValidationError

from dora_api.infrastructure.api_response import (ProblemDetails, bad_request,
                                                  unauthorized)
from dora_api.infrastructure.decorators import REQUEST_BODYS_BY_ENDPOINT


_Logger = logging.getLogger(__name__)
MIDDLEWARE = Blueprint('MIDDLEWARE', __name__)


# Endpoints that don't require an authenticated session. Anything under /api/
# that isn't listed here is gated by the require_auth hook below.
PUBLIC_ENDPOINTS = frozenset({
    "login",
    "register_user",
    "health_check",   # health probes must not require auth (used by container orchestrators)
})


@MIDDLEWARE.before_app_request
def handle_incoming_request():
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
