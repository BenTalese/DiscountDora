"""C-9.8 — Web Push sender (RFC 8030 + VAPID).

Wraps `pywebpush` so the rest of the codebase doesn't import a third-
party HTTP client. Mirrors `email_sender.py` shape: a single send_*
function, a dry-run mode when the install isn't configured, and the
config read in one place.

VAPID config from env (same shape as the SMTP block):
  DORA_VAPID_PUBLIC_KEY    base64url-encoded uncompressed P-256 public
                           key (the value the SPA passes as
                           `applicationServerKey` to
                           `pushManager.subscribe`). Required for real
                           sends.
  DORA_VAPID_PRIVATE_KEY   matching private key (PEM or base64url). The
                           server signs the JWT in each push request's
                           Authorization header with this.
  DORA_VAPID_SUBJECT       contact `mailto:` or `https://` URL the
                           push service uses to reach the admin if
                           something goes wrong (RFC 8292 §2).
                           Default: `mailto:admin@dora.local`.

When any of public/private is missing the sender is in **dry-run** mode
(logs the push, returns success). This keeps an unconfigured self-hosted
install bootable and lets developers test the surrounding plumbing
without generating keys.

Generate a key pair with `py-vapid`'s CLI (bundled with pywebpush):
    python -m py_vapid --gen --applicationServerKey
which prints the public key + writes `private_key.pem`.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from pywebpush import WebPushException, webpush


@dataclass(slots=True)
class _VapidConfig:
    public_key: str
    private_key: str
    subject: str
    dry_run: bool


def _config() -> _VapidConfig:
    # FU-333 Bucket B — public_key + subject resolve through the
    # AppSetting-first resolver. Private key stays env-only (Bucket C).
    try:
        from dora_api.features.app_settings.operational_config import \
            resolved_operational_config
        op = resolved_operational_config()
        public_key = op.vapid_public_key
        subject = op.vapid_subject or "mailto:admin@dora.local"
    except Exception:
        public_key = os.environ.get("DORA_VAPID_PUBLIC_KEY", "").strip()
        subject = os.environ.get("DORA_VAPID_SUBJECT", "mailto:admin@dora.local").strip() \
            or "mailto:admin@dora.local"
    private_key = os.environ.get("DORA_VAPID_PRIVATE_KEY", "").strip()
    return _VapidConfig(
        public_key=public_key,
        private_key=private_key,
        subject=subject,
        # Either half missing → can't sign / can't be subscribed to →
        # dry-run. The frontend toggle is independently gated on the
        # health flag, so this only matters if someone hand-edits a
        # subscription row.
        dry_run=not (public_key and private_key),
    )


def is_configured() -> bool:
    """True when both VAPID halves are set. Read by the health endpoint
    so the SPA's R-014 gating reflects whether real pushes can leave the
    box."""
    return not _config().dry_run


def vapid_public_key() -> str | None:
    """Public key the SPA needs for `pushManager.subscribe({applicationServerKey})`.
    Returns None when VAPID isn't configured (the SPA treats that as
    "push channel disabled" and shows the toggle as disabled)."""
    cfg = _config()
    return cfg.public_key or None


class PushGoneError(Exception):
    """The subscription endpoint is permanently gone (HTTP 404/410). The
    caller should delete the row — the browser unregistered or the
    user revoked permission. Distinct from a transient 5xx so the job
    can prune without retrying."""


def send_push(
    *,
    endpoint: str,
    p256dh: str,
    auth: str,
    payload: dict[str, Any],
) -> None:
    """Send a single push synchronously. Raises `PushGoneError` for
    permanent failures (so the caller can drop the subscription row),
    or `WebPushException` for transient errors. In dry-run mode this is
    a no-op apart from a log line."""
    log = logging.getLogger(__name__)
    cfg = _config()
    if cfg.dry_run:
        log.info(
            "DRY-RUN push | endpoint=%s | payload=%s",
            endpoint, json.dumps(payload, default=str),
        )
        return
    try:
        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {"p256dh": p256dh, "auth": auth},
            },
            data=json.dumps(payload, default=str),
            vapid_private_key=cfg.private_key,
            vapid_claims={"sub": cfg.subject},
            # 24h TTL keeps a quiet device able to wake to an alert that
            # was queued while it was offline; longer than that and the
            # alert state is likely stale anyway.
            ttl=86400,
        )
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (404, 410):
            raise PushGoneError(endpoint) from exc
        raise
