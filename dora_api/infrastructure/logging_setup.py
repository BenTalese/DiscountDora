"""Structured logging configuration shared across every service.

Each service calls `configure_logging("dapi", ...)` exactly once at
startup. The function is idempotent: re-calls clear and rebuild the
handlers, which makes restart-during-tests safe.

Formatter:
    %(asctime)s %(levelname)s [%(name)s] [req=%(request_id)s] [user=%(user_id)s] %(message)s

Handlers:
    stdout         — for docker-style log aggregation.
    RotatingFile   — ${log_dir}/<service>.log, 10 MB × 5 backups.

Level:
    INFO by default, DEBUG when `debug=True` is passed (typically when
    DORA_CONFIG.is_debug_mode_enabled() is true).

Noise control:
    sqlalchemy.engine is pinned to WARNING regardless of root — its
    INFO/DEBUG output is the raw SQL stream, which is overwhelming and
    only useful when actively debugging a query.
    werkzeug stays at WARNING in production runs (its INFO is one line
    per request, which we already log ourselves via the middleware).
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dora_api.infrastructure.log_context import LogContextFilter


_FORMAT = (
    "%(asctime)s %(levelname)-7s [%(name)s] "
    "[req=%(request_id)s] [user=%(user_id)s] %(message)s"
)

# 10 MB per file, 5 files = 50 MB historic per service.
_FILE_MAX_BYTES = 10 * 1024 * 1024
_FILE_BACKUP_COUNT = 5


def configure_logging(
    service_name: str,
    log_dir: Path | str,
    *,
    debug: bool = False,
    quiet_modules: tuple[str, ...] = ("sqlalchemy.engine",),
    werkzeug_level: int = logging.WARNING,
) -> None:
    """Wire stdout + rotating-file handlers on the root logger with the
    request-context filter. Safe to call more than once.

    Args:
        service_name: Short identifier ("dapi", "mapi", "emailer"). Used
            for the log file name.
        log_dir: Directory the rotating log file goes in. Created if
            missing.
        debug: Pull root + module loggers up to DEBUG. Off in production.
        quiet_modules: Loggers pinned to WARNING regardless of root. The
            default silences SQLAlchemy's raw-SQL echo.
        werkzeug_level: Override the Werkzeug request-log level. Defaults
            to WARNING because the request middleware already emits an
            equivalent line.
    """
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    # Replace existing handlers so re-invocation (tests, dev reloads)
    # doesn't accumulate duplicates.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    root.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = logging.Formatter(_FORMAT)
    context_filter = LogContextFilter()

    stream = logging.StreamHandler(stream=sys.stdout)
    stream.setFormatter(formatter)
    stream.addFilter(context_filter)
    root.addHandler(stream)

    rotating = RotatingFileHandler(
        log_dir_path / f"{service_name}.log",
        maxBytes=_FILE_MAX_BYTES,
        backupCount=_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    rotating.setFormatter(formatter)
    rotating.addFilter(context_filter)
    root.addHandler(rotating)

    for name in quiet_modules:
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(werkzeug_level)
