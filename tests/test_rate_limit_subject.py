"""FU-458 — the per-`subject` bucket key on the rate limiter.

Locks in the two-line behavioural contract:

1. Passing `subject="alice"` and `subject="bob"` gets independent
   buckets — a shared household IP can't cause one user's traffic to
   count against another's. That's the whole point of the FU.

2. Omitting `subject` (or passing None) keeps the historical
   per-IP semantics so the auth surface's pre-auth callers
   (login/register/verify) stay unchanged.

No DB, no HTTP — the limiter is a pure in-memory bucket, so we test
it directly.
"""
from __future__ import annotations

import time

from dora_api.infrastructure import auth_helpers
from dora_api.infrastructure.auth_helpers import (
    rate_limit, rate_limit_remaining_seconds,
)


def _reset_buckets() -> None:
    """Tests share the process-wide bucket dict; wipe between cases so
    ordering can't leak."""
    with auth_helpers._buckets_lock:
        auth_helpers._buckets.clear()


# ── subject-keyed isolation ─────────────────────────────────────────────

def test__subject_buckets_are_independent():
    _reset_buckets()
    # Alice fills her bucket exactly to the limit — all three succeed…
    assert rate_limit("fu458.iso", 3, subject="alice") is True
    assert rate_limit("fu458.iso", 3, subject="alice") is True
    assert rate_limit("fu458.iso", 3, subject="alice") is True
    # …and the fourth is refused.
    assert rate_limit("fu458.iso", 3, subject="alice") is False
    # Bob's own bucket is untouched — this is the household-shared-IP
    # scenario the FU exists for.
    assert rate_limit("fu458.iso", 3, subject="bob") is True


def test__scope_isolates_buckets_within_a_single_subject():
    _reset_buckets()
    # Same subject, different scopes → independent buckets.
    assert rate_limit("fu458.a", 1, subject="alice") is True
    assert rate_limit("fu458.a", 1, subject="alice") is False
    # A separate scope keeps its own count regardless of `a`'s
    # exhausted bucket.
    assert rate_limit("fu458.b", 1, subject="alice") is True


def test__remaining_seconds_reflects_the_subject_bucket():
    _reset_buckets()
    # Fill alice's bucket to the ceiling; her retry-after is > 0.
    assert rate_limit("fu458.retry", 1, subject="alice") is True
    assert rate_limit("fu458.retry", 1, subject="alice") is False
    assert rate_limit_remaining_seconds("fu458.retry", 1, subject="alice") > 0
    # Bob's untouched bucket returns 0 — no wait for him.
    assert rate_limit_remaining_seconds("fu458.retry", 1, subject="bob") == 0


# ── back-compat: subject=None falls back to per-IP bucketing ────────────

def test__subject_none_falls_back_to_ip_key(monkeypatch):
    """Pre-auth callers (login, register, verify) don't have a user_id
    to pass; the helper must still bucket per-IP for them the way it
    always did."""
    _reset_buckets()

    # `_bucket_key` reaches for `request.remote_addr` when subject is
    # None. Outside a Flask request context it catches the
    # RuntimeError and settles on "anon" — good enough for a unit
    # test because the same key comes back both calls.
    assert rate_limit("fu458.iponly", 2) is True
    assert rate_limit("fu458.iponly", 2) is True
    assert rate_limit("fu458.iponly", 2) is False
    # And an explicit-subject call for the same scope must NOT share
    # the anon bucket — that would defeat the whole point.
    assert rate_limit("fu458.iponly", 2, subject="alice") is True


def test__malformed_subject_still_isolates_the_key():
    """Callers occasionally pass empty strings when the session lacks
    a user_id. Empty string is falsy → treated the same as None (IP
    fallback). Documents the boundary."""
    _reset_buckets()
    assert rate_limit("fu458.empty", 1, subject="") is True
    # Empty string routes through the ip-fallback branch, so a second
    # call in the same "anon" IP context exhausts it.
    assert rate_limit("fu458.empty", 1, subject="") is False
    # Passing a real subject afterward gets its own bucket regardless.
    assert rate_limit("fu458.empty", 1, subject="alice") is True
