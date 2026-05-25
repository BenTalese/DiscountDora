"""POST /api/client-logs — frontend ships errors here so client crashes
land in the same log stream as server errors.

The SPA's `useClientLogger` composable calls this on `error` / `warn`.
The handler does a tiny per-session token-bucket rate limit so a runaway
error loop in the browser doesn't flood the log file (which would also
roll over noisier sibling messages out of the rotation window).

In a follow-up round (audit log) this will also persist to the
audit_events table with source=web, action="client.error".
"""
import logging
import time
from collections import deque
from threading import Lock

from flask import request, session
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.audit_event import (
    SEVERITY_ERROR, SEVERITY_INFO, SEVERITY_WARN, SOURCE_WEB,
)
from dora_api.features.routers import CLIENT_LOGS_ROUTER
from dora_api.infrastructure.api_response import bad_request, no_content
from dora_api.infrastructure.audit import emit as audit_emit
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body


_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}

# Rate limit: max 10 events per 60 second window per session. Token-bucket
# implementation via a sliding window of timestamps. In-memory — restarts
# zero the buckets, which is fine for what's effectively a denial-of-log
# guard rail.
_BUCKET_WINDOW_SECONDS = 60.0
_BUCKET_MAX_EVENTS = 10
_buckets: dict[str, deque[float]] = {}
_buckets_lock = Lock()


class SubmitClientLogRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: str = Field(min_length=1, max_length=16)
    message: str = Field(min_length=1, max_length=2048)
    # Best-effort breadcrumbs the SPA can attach: route, component name,
    # stack trace excerpt, user-agent. Capped overall payload size is
    # enforced by Pydantic field-length above + this dict being free-form.
    context: dict | None = None


def _client_bucket_key() -> str:
    """Bucket by session id when authed, otherwise by remote IP. Cookies
    aren't a perfect identifier but this is a noise-control bucket, not
    a security perimeter."""
    return session.get("user_id") or request.remote_addr or "anon"


def _allow(key: str) -> bool:
    now = time.monotonic()
    with _buckets_lock:
        bucket = _buckets.setdefault(key, deque())
        # Drop timestamps older than the window so the deque stays small.
        cutoff = now - _BUCKET_WINDOW_SECONDS
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= _BUCKET_MAX_EVENTS:
            return False
        bucket.append(now)
        return True


@CLIENT_LOGS_ROUTER.route("", methods=["POST"])
@has_request_body(SubmitClientLogRequest)
def submit_client_log():
    req: SubmitClientLogRequest = get_request_body()
    level = _LEVELS.get(req.level.strip().lower())
    if level is None:
        return bad_request(
            f"Unknown level '{req.level}'. Use one of "
            f"{', '.join(sorted(_LEVELS.keys()))}."
        )

    if not _allow(_client_bucket_key()):
        # 429 isn't fatal for the SPA — it'll back off and try again
        # later. We don't bother logging a server-side line about the
        # drop; that'd defeat the point of the rate limit.
        return no_content()

    logger = logging.getLogger("client")
    logger.log(
        level,
        "client: %s",
        req.message,
        extra={"client_context": req.context or {}},
    )

    # Persist to the audit log for the admin view. ERROR/WARN client
    # events are the ones admins actually want to see; INFO/DEBUG stay
    # in the regular log stream only.
    if level >= logging.WARNING:
        severity = SEVERITY_ERROR if level >= logging.ERROR else SEVERITY_WARN
        audit_emit(
            "client.error" if severity == SEVERITY_ERROR else "client.warning",
            source=SOURCE_WEB,
            severity=severity,
            payload={"message": req.message, "context": req.context},
        )
    else:
        # Surface INFO-level client beacons too, but at lower severity so
        # admin-UI filters can hide them by default.
        audit_emit(
            "client.info",
            source=SOURCE_WEB,
            severity=SEVERITY_INFO,
            payload={"message": req.message, "context": req.context},
        )
    return no_content()
