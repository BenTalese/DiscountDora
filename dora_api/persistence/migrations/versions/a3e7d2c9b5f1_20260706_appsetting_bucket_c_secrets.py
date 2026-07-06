"""20260706_appsetting_bucket_c_secrets

FU-333 Bucket C — encrypted-at-rest storage for the two operational secrets
that Bucket B (2026-07-05) left env-only: the SMTP password and the VAPID
private key. Both are wrapped with the Fernet helper from FU-153
(``infrastructure/llm/key_encryption``) using ``DORA_LLM_KEY_ENCRYPTION_KEY``
as the wrapping key, and stored as base64-safe strings on the singleton
``AppSetting`` row.

Same migration also closes out Buckets B + D:

* **Bucket B env fallbacks** — dropped 2026-07-06 (pre-release; no operators
  to preserve). The resolver
  (``dora_api/features/app_settings/operational_config.py``) is now a
  straight ``AppSetting`` projection; the previously-committed migration
  ``b7d2f9c1e4a3`` still adds the 12 Bucket B columns but its env→row
  backfill is now a dead-code moment-in-time artifact for anyone replaying
  the chain.
* **Bucket D desktop first-run** — implemented in ``desktop_app.py``'s
  ``_bootstrap_keys`` rather than the schema; nothing to migrate. Comment
  here so future readers grepping the schema for FU-333 find the pointer.

Revision ID: a3e7d2c9b5f1
Revises: c4e9a2f7b1d3
Create Date: 2026-07-06 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'a3e7d2c9b5f1'
down_revision = 'c4e9a2f7b1d3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column('smtp_password_encrypted', sa.String(1024), nullable=False, server_default=""))
        batch.add_column(sa.Column('vapid_private_key_encrypted', sa.String(4096), nullable=False, server_default=""))


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('vapid_private_key_encrypted')
        batch.drop_column('smtp_password_encrypted')
