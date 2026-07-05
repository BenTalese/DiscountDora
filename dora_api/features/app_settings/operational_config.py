"""FU-333 Bucket B — resolver for the operational config that was formerly
carried by ``DORA_*`` env vars.

For each field: **prefer the ``AppSetting`` value when it is non-empty /
non-default; otherwise fall back to the historic env var.** This lets an
operator whose SMTP is configured via env keep working after upgrade
without any admin action, while a fresh install (empty row, no env) lands
on the seeded defaults from the ``AppSetting`` entity.

The env fallback is a one-release deprecation window. A follow-up opened at
merge time will drop the ``os.environ`` reads here and at the seven call
sites — after that, this module becomes a straight ``AppSetting.x``
projection.

Why a resolver at all (rather than each site reading ``AppSetting`` directly):
several of the call sites are hot paths (``email_sender``, ``push_sender``,
``tts_synthesize``) where a repository round-trip per send is wasted work.
The resolver builds a small immutable dataclass per call so the call site
gets typed field access without repeatedly hitting the DB.

Bootstrap-only env vars (``DORA_SECRET_KEY``, ``DORA_LLM_KEY_ENCRYPTION_KEY``,
``DORA_ENV``, ``DORA_SECURE_COOKIES``, ``DORA_SPA_DIR``,
``DORA_SKIP_PROD_VALIDATION``, ``DORA_ALLOW_DESTRUCTIVE``) are *not* handled
here — they're read before the DB is reachable, so they must stay in env by
design. Same for the two Bucket-C secrets: ``DORA_SMTP_PASSWORD`` and
``DORA_VAPID_PRIVATE_KEY`` remain env-only until encrypted-in-DB storage
lands.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class OperationalConfig:
    """Resolved operational config. See module docstring for precedence rules."""
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_from: str
    smtp_use_tls: bool
    vapid_public_key: str
    vapid_subject: str
    piper_bin: str
    piper_bundled_voice_dir: str
    piper_voice: str
    email_enabled: bool
    audit_retention_days: int
    public_url: str


_UNSET = object()


def _pick_str(row_value: str | None, env_name: str, default: str) -> str:
    """Non-empty AppSetting wins; else env if set + non-empty; else seeded default."""
    if row_value:
        stripped = row_value.strip()
        if stripped:
            return stripped
    env_value = os.environ.get(env_name)
    if env_value is not None:
        stripped = env_value.strip()
        if stripped:
            return stripped
    return default


def _pick_int(row_value: int | None, env_name: str, default: int) -> int:
    """Row value used if not None; else env parsed; else default. Ints don't
    have a "non-empty" concept the way strings do — an explicit 0 is a real
    setting, so we don't treat it as unset. The seeded defaults in the entity
    match the historic env defaults, so a fresh install still lands correctly
    when both are absent."""
    if row_value is not None:
        return int(row_value)
    env_value = os.environ.get(env_name)
    if env_value is not None:
        try:
            return int(env_value.strip())
        except ValueError:
            pass
    return default


def _pick_bool(row_value: object, env_name: str, default: bool) -> bool:
    """Bools carry no "unset" state in the schema (NOT NULL + server_default),
    so the row always wins over the env. We keep the env parameter for
    documentation + parity with the string/int helpers, but only consult it
    if the row is missing entirely (defensive — shouldn't happen for a
    materialised AppSetting row)."""
    if row_value is _UNSET:
        env_value = os.environ.get(env_name)
        if env_value is not None:
            return env_value.strip().lower() in ("1", "true", "yes", "on")
        return default
    return bool(row_value)


def resolved_operational_config() -> OperationalConfig:
    """Read the singleton ``AppSetting`` row + apply env fallbacks. Callers
    treat the returned dataclass as immutable for the duration of one
    request/job. A background job that spans hours should call this again
    per work unit rather than caching the result across the whole process
    (admin-driven config changes should take effect on the next request)."""
    row = get_or_create_app_setting(SqlAlchemyRepository())
    return OperationalConfig(
        smtp_host=_pick_str(getattr(row, "smtp_host", ""), "DORA_SMTP_HOST", ""),
        smtp_port=_pick_int(getattr(row, "smtp_port", 587), "DORA_SMTP_PORT", 587),
        smtp_username=_pick_str(getattr(row, "smtp_username", ""), "DORA_SMTP_USERNAME", ""),
        smtp_from=_pick_str(getattr(row, "smtp_from", ""), "DORA_SMTP_FROM", ""),
        smtp_use_tls=_pick_bool(getattr(row, "smtp_use_tls", _UNSET), "DORA_SMTP_USE_TLS", True),
        vapid_public_key=_pick_str(getattr(row, "vapid_public_key", ""), "DORA_VAPID_PUBLIC_KEY", ""),
        vapid_subject=_pick_str(getattr(row, "vapid_subject", ""), "DORA_VAPID_SUBJECT", "mailto:admin@dora.local"),
        piper_bin=_pick_str(getattr(row, "piper_bin", ""), "DORA_PIPER_BIN", ""),
        piper_bundled_voice_dir=_pick_str(getattr(row, "piper_bundled_voice_dir", ""), "DORA_PIPER_BUNDLED_VOICE_DIR", ""),
        piper_voice=_pick_str(getattr(row, "piper_voice", ""), "DORA_PIPER_VOICE", ""),
        email_enabled=_pick_bool(getattr(row, "email_enabled", _UNSET), "DORA_EMAIL_ENABLED", False),
        audit_retention_days=_pick_int(getattr(row, "audit_retention_days", 365), "DORA_AUDIT_RETENTION_DAYS", 365),
        public_url=_pick_str(getattr(row, "public_url", ""), "DORA_PUBLIC_URL", ""),
    )
