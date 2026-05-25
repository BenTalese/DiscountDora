"""Nightly job that prunes AuditEvent rows older than RETENTION_DAYS.

Wired in startup.py via APScheduler. Job is no-op when the table is
empty and never raises (a failure here must not take the API down).
RETENTION_DAYS defaults to 365; override with the DORA_AUDIT_RETENTION_DAYS
env var.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from dora_api.app import app, db


DEFAULT_RETENTION_DAYS = 365


def retention_days() -> int:
    try:
        value = int(os.environ.get("DORA_AUDIT_RETENTION_DAYS", DEFAULT_RETENTION_DAYS))
    except ValueError:
        return DEFAULT_RETENTION_DAYS
    return max(1, value)


def prune_audit_events() -> int:
    """Delete events older than the retention cut-off. Returns the count
    deleted. Wrapped in app.app_context so it can run from APScheduler
    threads outside an HTTP request."""
    log = logging.getLogger(__name__)
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days())
    try:
        with app.app_context():
            table = db.metadata.tables["AuditEvent"]
            result = db.session.execute(
                delete(table).where(table.c.occurred_at < cutoff),
            )
            db.session.commit()
            deleted = result.rowcount or 0
            if deleted:
                log.info(
                    "Audit retention pruned %d event(s) older than %s",
                    deleted, cutoff.isoformat(),
                )
            return deleted
    except Exception as exc:  # noqa: BLE001
        log.warning("Audit retention prune failed: %s", exc)
        return 0
