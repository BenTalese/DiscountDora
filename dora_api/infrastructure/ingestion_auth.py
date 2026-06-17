"""Bearer-token auth lane for `POST /api/ingest` (C-10.1).

The ingestion endpoint is exempt from the session-cookie middleware: an
external producer can't carry a `dora_session` cookie. It instead sends
`Authorization: Bearer <key>` with a raw key minted on the admin "API
access" page; the key's SHA-256 hash lives in `IngestionSource`. This
module mirrors `auth_helpers._hash_token` (R-003 — one hashing path)
and gives `/api/ingest` a single place to validate the header.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from flask import request
from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.ingestion_source import IngestionSource


def hash_ingestion_key(raw: str) -> str:
    """SHA-256 hex digest. Mirrors `auth_helpers._hash_token`."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def mint_ingestion_key() -> str:
    """Generate a fresh raw key for a new IngestionSource. The caller
    persists the hash and returns the raw value to the admin exactly
    once."""
    return secrets.token_urlsafe(32)


def find_ingestion_source(raw_key: str) -> IngestionSource | None:
    """Return the enabled `IngestionSource` matching `raw_key`, or None
    if absent / disabled. Uses `hmac.compare_digest` on the hex digest
    so timing doesn't leak hash candidates.
    """
    if not raw_key:
        return None
    table = db.metadata.tables["IngestionSource"]
    candidate_hash = hash_ingestion_key(raw_key)
    rows = db.session.execute(
        select(table).where(table.c.enabled.is_(True))
    ).mappings().all()
    for row in rows:
        if hmac.compare_digest(row["key_hash"], candidate_hash):
            return db.session.get(IngestionSource, row["id"])
    return None


def extract_bearer_token() -> str | None:
    """Pull the raw token out of `Authorization: Bearer <key>`. Returns
    None on anything else (missing header, wrong scheme, empty value)."""
    header = request.headers.get("Authorization", "")
    if not header:
        return None
    parts = header.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def stamp_used(source: IngestionSource) -> None:
    """Update `last_used_at` to now. Callers commit alongside their own
    write so the bump is atomic with the ingest result."""
    source.last_used_at = datetime.now(timezone.utc)
