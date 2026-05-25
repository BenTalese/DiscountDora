import logging
import time
from uuid import uuid4

from flask import Blueprint, g, request

from dora_api.infrastructure.log_context import reset_context, set_request_id

# The Flask-CORS extension (configured in startup.py) handles preflight
# (OPTIONS) requests automatically — including writing the
# Access-Control-Allow-* headers on the response. A previous incarnation of
# this blueprint short-circuited OPTIONS with a JSON body whose keys looked
# like CORS headers, which silently broke the actual headers.
MIDDLEWARE = Blueprint('MIDDLEWARE', __name__)


_Logger = logging.getLogger(__name__)


@MIDDLEWARE.before_app_request
def stamp_context():
    incoming = request.headers.get("X-Request-Id")
    request_id = incoming.strip() if incoming else uuid4().hex
    set_request_id(request_id)
    g.request_id = request_id
    g.request_started_at = time.perf_counter()
    if _Logger.isEnabledFor(logging.INFO):
        _Logger.info("→ %s %s", request.method, request.path)


@MIDDLEWARE.after_app_request
def stamp_request_id(response):
    started = getattr(g, "request_started_at", None)
    request_id = getattr(g, "request_id", None)
    if request_id:
        response.headers["X-Request-Id"] = request_id
    if started is not None and _Logger.isEnabledFor(logging.INFO):
        duration_ms = (time.perf_counter() - started) * 1000.0
        _Logger.info(
            "← %d %s %s (%.1fms)",
            response.status_code, request.method, request.path, duration_ms,
        )
    return response


@MIDDLEWARE.teardown_app_request
def clear_context(_exc):
    reset_context()
