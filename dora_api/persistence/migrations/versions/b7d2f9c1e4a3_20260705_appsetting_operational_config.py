"""20260705_appsetting_operational_config

FU-333 Bucket B — promote 12 operational `DORA_*` env vars to columns on
``AppSetting`` so an admin can configure a fresh install through
Settings → Admin → System instead of editing an environment file. See
``docs/04_proposals/IMPL_PLAN_ENV_TO_APPSETTING.md``.

Bootstrap vars (SECRET_KEY, LLM_KEY_ENCRYPTION_KEY, ENV, SECURE_COOKIES,
SPA_DIR, SKIP_PROD_VALIDATION, ALLOW_DESTRUCTIVE) stay in env — they're
read before the DB is reachable, or they are the root key that decrypts
DB rows. Bucket C secrets (SMTP password, VAPID private key) also stay
in env for now; the encrypted-in-DB storage lands with a follow-up.

Columns added (12), matching entity field names in
``dora_api/domain/entities/app_setting.py``:

* ``smtp_host``, ``smtp_port``, ``smtp_username``, ``smtp_from``,
  ``smtp_use_tls`` — was ``DORA_SMTP_HOST`` / ``_PORT`` / ``_USERNAME``
  / ``_FROM`` / ``_USE_TLS``.
* ``vapid_public_key``, ``vapid_subject`` — was
  ``DORA_VAPID_PUBLIC_KEY`` / ``_SUBJECT``.
* ``piper_bin``, ``piper_bundled_voice_dir`` — was
  ``DORA_PIPER_BIN`` / ``_BUNDLED_VOICE_DIR``.
* ``email_enabled``, ``audit_retention_days``, ``public_url`` — was
  ``DORA_EMAIL_ENABLED`` / ``_AUDIT_RETENTION_DAYS`` / ``_PUBLIC_URL``.

**One-shot env→row backfill.** Immediately after the columns exist, the
migration copies each env var (if set) into the singleton ``AppSetting``
row. This preserves an existing operator's SMTP / VAPID / TTS config
across upgrade — env-driven installs keep working without any admin
action. Fresh installs (no envs, empty row) start from the seeded
defaults. A future release will drop the env fallbacks entirely; the
resolver bridging period is documented in
``dora_api/features/app_settings/operational_config.py``.

Revision ID: b7d2f9c1e4a3
Revises: e5c8b3a1f4d2
Create Date: 2026-07-05 00:00:00.000000
"""
import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy import false, true


revision = 'b7d2f9c1e4a3'
down_revision = 'e5c8b3a1f4d2'
branch_labels = None
depends_on = None


def _bool_from_env(raw: str | None) -> bool | None:
    if raw is None:
        return None
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _int_from_env(raw: str | None) -> int | None:
    if raw is None or not raw.strip():
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column('smtp_host', sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column('smtp_port', sa.Integer(), nullable=False, server_default="587"))
        batch.add_column(sa.Column('smtp_username', sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column('smtp_from', sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column('smtp_use_tls', sa.Boolean(), nullable=False, server_default=true()))
        batch.add_column(sa.Column('vapid_public_key', sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column('vapid_subject', sa.String(255), nullable=False, server_default="mailto:admin@dora.local"))
        batch.add_column(sa.Column('piper_bin', sa.String(1024), nullable=False, server_default=""))
        batch.add_column(sa.Column('piper_bundled_voice_dir', sa.String(1024), nullable=False, server_default=""))
        batch.add_column(sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default=false()))
        batch.add_column(sa.Column('audit_retention_days', sa.Integer(), nullable=False, server_default="365"))
        batch.add_column(sa.Column('public_url', sa.String(500), nullable=False, server_default=""))

    # Env→row backfill. Only writes fields whose env var is actually set,
    # so a fresh install (no envs) lands on the seeded defaults above.
    env_map: list[tuple[str, str, object]] = [
        ("smtp_host", "DORA_SMTP_HOST", os.environ.get("DORA_SMTP_HOST")),
        ("smtp_port", "DORA_SMTP_PORT", _int_from_env(os.environ.get("DORA_SMTP_PORT"))),
        ("smtp_username", "DORA_SMTP_USERNAME", os.environ.get("DORA_SMTP_USERNAME")),
        ("smtp_from", "DORA_SMTP_FROM", os.environ.get("DORA_SMTP_FROM")),
        ("smtp_use_tls", "DORA_SMTP_USE_TLS", _bool_from_env(os.environ.get("DORA_SMTP_USE_TLS"))),
        ("vapid_public_key", "DORA_VAPID_PUBLIC_KEY", os.environ.get("DORA_VAPID_PUBLIC_KEY")),
        ("vapid_subject", "DORA_VAPID_SUBJECT", os.environ.get("DORA_VAPID_SUBJECT")),
        ("piper_bin", "DORA_PIPER_BIN", os.environ.get("DORA_PIPER_BIN")),
        ("piper_bundled_voice_dir", "DORA_PIPER_BUNDLED_VOICE_DIR", os.environ.get("DORA_PIPER_BUNDLED_VOICE_DIR")),
        ("email_enabled", "DORA_EMAIL_ENABLED", _bool_from_env(os.environ.get("DORA_EMAIL_ENABLED"))),
        ("audit_retention_days", "DORA_AUDIT_RETENTION_DAYS", _int_from_env(os.environ.get("DORA_AUDIT_RETENTION_DAYS"))),
        ("public_url", "DORA_PUBLIC_URL", os.environ.get("DORA_PUBLIC_URL")),
    ]

    bind = op.get_bind()
    for column, _env_name, value in env_map:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        bind.execute(
            sa.text(f'UPDATE "AppSetting" SET {column} = :v'),
            {"v": value},
        )


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('public_url')
        batch.drop_column('audit_retention_days')
        batch.drop_column('email_enabled')
        batch.drop_column('piper_bundled_voice_dir')
        batch.drop_column('piper_bin')
        batch.drop_column('vapid_subject')
        batch.drop_column('vapid_public_key')
        batch.drop_column('smtp_use_tls')
        batch.drop_column('smtp_from')
        batch.drop_column('smtp_username')
        batch.drop_column('smtp_port')
        batch.drop_column('smtp_host')
