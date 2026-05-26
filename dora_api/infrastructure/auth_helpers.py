"""Shared building blocks for the A1 auth surface.

All five new auth endpoints reuse this module:
  - Password rule validation (min 10 chars, ≥1 letter + ≥1 digit).
  - Token generation, hashing, persistence, and constant-time lookup.
  - Anti-enumeration helpers (always pretend success on
    forgot-password / resend-verification).
  - A tiny in-memory token-bucket rate limiter (per IP+route).
  - Public URL resolution so verification / reset links work for whatever
    deployment surface is in use — PWA on https://, a self-hosted desktop
    Electron app on file://-loaded code, or a mobile shell pointing at
    https://. Pulled from DORA_PUBLIC_URL with sensible fallbacks.

Tokens live in a single `AuthToken` table keyed by purpose, hashed at
rest (SHA-256). The raw token only appears in the outbound email. Token
consumption is a `consumed_at` stamp rather than a delete so audit
queries can still see what fired against the user.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any
from uuid import UUID, uuid4

from flask import request
from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.auth_token import (
    ALLOWED_PURPOSES, AuthToken, PURPOSE_RESET_PASSWORD, PURPOSE_VERIFY_EMAIL,
)


# ── Password rules ─────────────────────────────────────────────────────

MIN_PASSWORD_LENGTH = 10
_LETTER_RE = re.compile(r"[A-Za-z]")
_DIGIT_RE = re.compile(r"\d")

PASSWORD_RULES_DOC = (
    f"Password must be at least {MIN_PASSWORD_LENGTH} characters and "
    "include at least one letter and one digit."
)


def validate_password(value: str) -> str | None:
    """Returns an error message, or None if the password is acceptable."""
    if not value or len(value) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if not _LETTER_RE.search(value):
        return "Password must include at least one letter."
    if not _DIGIT_RE.search(value):
        return "Password must include at least one digit."
    return None


# ── Email format ───────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: str | None) -> bool:
    return bool(value) and bool(_EMAIL_RE.match(value or ""))


# ── Token plumbing ─────────────────────────────────────────────────────

# Defaults; the per-purpose TTLs match the brief.
VERIFY_EMAIL_TTL = timedelta(hours=24)
RESET_PASSWORD_TTL = timedelta(hours=1)
CHANGE_EMAIL_TTL = timedelta(hours=24)


def _hash_token(raw: str) -> str:
    """SHA-256 hex digest. Plenty for a single-use credential."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue_token(
    user_id: UUID,
    purpose: str,
    ttl: timedelta,
    payload: str | None = None,
) -> str:
    """Mint a new token for `user_id`, persist its hash, return the raw
    value. Caller is responsible for embedding the raw value in the
    outbound email.
    """
    assert purpose in ALLOWED_PURPOSES, f"unknown purpose {purpose!r}"
    raw = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    row = AuthToken(
        id=uuid4(),
        user_id=user_id,
        token_hash=_hash_token(raw),
        purpose=purpose,
        payload=payload,
        expires_at=now + ttl,
        created_at=now,
        consumed_at=None,
    )
    db.session.add(row)
    db.session.commit()
    return raw


def find_active_token(raw: str, purpose: str) -> AuthToken | None:
    """Look up a fresh, unconsumed, in-date token of the given purpose
    using a constant-time hash comparison (the SHA-256 itself is
    deterministic; we use `hmac.compare_digest` on the hex digest so
    timing attacks don't leak hash candidates).
    """
    if not raw:
        return None
    table = db.metadata.tables["AuthToken"]
    candidate_hash = _hash_token(raw)
    now = datetime.now(timezone.utc)
    rows = db.session.execute(
        select(table).where(
            table.c.purpose == purpose,
            table.c.consumed_at.is_(None),
            table.c.expires_at > now,
        )
    ).mappings().all()
    for row in rows:
        if hmac.compare_digest(row["token_hash"], candidate_hash):
            return AuthToken(
                id=row["id"],
                user_id=row["user_id"],
                token_hash=row["token_hash"],
                purpose=row["purpose"],
                payload=row["payload"],
                expires_at=row["expires_at"],
                created_at=row["created_at"],
                consumed_at=row["consumed_at"],
            )
    return None


def consume_token(token_id: UUID) -> None:
    table = db.metadata.tables["AuthToken"]
    db.session.execute(
        table.update().where(table.c.id == token_id).values(
            consumed_at=datetime.now(timezone.utc),
        )
    )
    db.session.commit()


def revoke_tokens_for_user(user_id: UUID, purpose: str) -> None:
    """Mark every still-live token of the given purpose consumed. Called
    after a successful password reset so any unused reset links go cold.
    """
    table = db.metadata.tables["AuthToken"]
    db.session.execute(
        table.update().where(
            table.c.user_id == user_id,
            table.c.purpose == purpose,
            table.c.consumed_at.is_(None),
        ).values(consumed_at=datetime.now(timezone.utc))
    )
    db.session.commit()


# ── Public URL resolution ──────────────────────────────────────────────

def public_base_url() -> str:
    """Where the SPA lives on the public internet. Used to build the
    URL embedded in verify-email / reset-password emails.

    Resolution order:
      1. DORA_PUBLIC_URL env var (canonical for any prod deployment —
         PWA host, mobile-app deeplink universal-link domain, desktop
         app's hosted shell, etc.).
      2. Origin header on the current request (the SPA POSTing to the
         API is the most reliable dev fallback).
      3. http://localhost:5174 (Quasar's default dev port).
    """
    explicit = os.environ.get("DORA_PUBLIC_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    try:
        origin = request.headers.get("Origin")
        if origin:
            return origin.rstrip("/")
    except RuntimeError:
        # Outside a request context (e.g. scheduler) — fall through.
        pass
    return "http://localhost:5174"


def build_verify_url(token: str) -> str:
    return f"{public_base_url()}/verify-email?token={token}"


def build_reset_url(token: str) -> str:
    return f"{public_base_url()}/reset-password?token={token}"


# ── Rate limiter ───────────────────────────────────────────────────────

# Per-route per-IP token bucket. In-memory and process-local — fine for
# a self-contained desktop install, a single PWA backend, or one mobile
# API host. For horizontally-scaled deployments swap for Redis later.
_buckets: dict[tuple[str, str], deque[float]] = {}
_buckets_lock = Lock()


def _bucket_key(scope: str) -> tuple[str, str]:
    ip = "anon"
    try:
        ip = request.remote_addr or "anon"
    except RuntimeError:
        pass
    return (scope, ip)


def rate_limit(scope: str, max_per_minute: int) -> bool:
    """Returns True if the call is within the limit, False otherwise.
    `scope` should be the endpoint identifier ("auth.login",
    "auth.register", …) so different routes don't share buckets.
    """
    key = _bucket_key(scope)
    now = time.monotonic()
    with _buckets_lock:
        bucket = _buckets.setdefault(key, deque())
        cutoff = now - 60.0
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= max_per_minute:
            return False
        bucket.append(now)
        return True


def rate_limit_remaining_seconds(scope: str, max_per_minute: int) -> int:
    """Seconds until the oldest event in the bucket falls outside the
    sliding window. Used for the Retry-After response header."""
    key = _bucket_key(scope)
    now = time.monotonic()
    with _buckets_lock:
        bucket = _buckets.get(key)
        if not bucket or len(bucket) < max_per_minute:
            return 0
        return max(0, int(60.0 - (now - bucket[0])) + 1)


# ── Helpers used across endpoints ──────────────────────────────────────

def normalise_email(value: str | None) -> str | None:
    return value.strip().lower() if value else None


_Logger = logging.getLogger(__name__)


def try_send(send_fn, *args, **kwargs) -> None:
    """Wrap an outbound email send so a misconfigured SMTP doesn't fail
    the originating request. We deliberately swallow + log — telling
    the user "couldn't send mail" would also reveal whether their email
    address is known to the system."""
    try:
        send_fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        _Logger.warning("auth email send failed: %s", exc)


# Re-export so callers don't have to know the underlying entity layout.
__all__ = [
    "MIN_PASSWORD_LENGTH", "PASSWORD_RULES_DOC", "validate_password",
    "is_valid_email", "normalise_email",
    "VERIFY_EMAIL_TTL", "RESET_PASSWORD_TTL", "CHANGE_EMAIL_TTL",
    "PURPOSE_VERIFY_EMAIL", "PURPOSE_RESET_PASSWORD",
    "issue_token", "find_active_token", "consume_token",
    "revoke_tokens_for_user",
    "public_base_url", "build_verify_url", "build_reset_url",
    "rate_limit", "rate_limit_remaining_seconds",
    "try_send",
]
