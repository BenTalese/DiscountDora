"""Request-scoped logging context.

Each incoming HTTP request stamps `request_id` (X-Request-Id header or a
fresh UUID4) and, if authed, `user_id` into contextvars. A logging.Filter
copies those onto every LogRecord so the per-service formatter can
include them — the rest of the codebase just uses `logging.getLogger(...)`
and the IDs flow through automatically.

contextvars rather than thread-locals so async handlers and APScheduler
jobs Just Work without manual plumbing.
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any


# Each var defaults to "-" so log lines without an active request still
# format cleanly (e.g. APScheduler ticks, startup messages).
_REQUEST_ID: ContextVar[str] = ContextVar("dora_request_id", default="-")
_USER_ID: ContextVar[str] = ContextVar("dora_user_id", default="-")


def set_request_id(value: str | None) -> None:
    _REQUEST_ID.set(value or "-")


def set_user_id(value: Any | None) -> None:
    _USER_ID.set(str(value) if value is not None else "-")


def get_request_id() -> str:
    return _REQUEST_ID.get()


def get_user_id() -> str:
    return _USER_ID.get()


def reset_context() -> None:
    _REQUEST_ID.set("-")
    _USER_ID.set("-")


class LogContextFilter(logging.Filter):
    """Copy the active request_id / user_id onto each LogRecord so the
    formatter can interpolate them without every call site passing them
    by hand.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _REQUEST_ID.get()
        record.user_id = _USER_ID.get()
        return True
