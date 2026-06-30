"""20260629_per_user_llm_config

FU-153 / DORA_ASSISTANT_ARCHITECTURE_PROPOSAL §7.1 + §7.4 — collapse the
install-wide LLM config into a per-user one, keep one install-wide
master kill-switch, and add the columns the multi-provider abstraction
(§7.4) needs.

Pre-release semantics (no production data to preserve):
  - **Drop** ``AppSetting.llm_enabled``, ``llm_base_url``, ``llm_model``.
  - **Add** ``AppSetting.master_llm_enabled BOOL NOT NULL DEFAULT 1``
    — the install-wide defence-in-depth toggle. An admin flipping
    this off forces every user's AI mode off regardless of their
    per-user setting.
  - **Add** to ``User``:
      ``llm_enabled``  BOOL  NOT NULL DEFAULT 0
      ``llm_provider`` VARCHAR(16) NULL   (closed-set R-010: 'ollama' |
                                             'openai' | 'anthropic' |
                                             'gemini'; validated at the
                                             update_me boundary)
      ``llm_base_url`` VARCHAR(500) NULL
      ``llm_model``    VARCHAR(255) NULL
      ``llm_api_key_encrypted`` BLOB NULL  — Fernet ciphertext; plaintext
                                             never leaves the request
                                             handler that writes it. See
                                             ``infrastructure.llm.key_encryption``.

The old admin-side AssistantSettings page collapses to a single
master-toggle row. Each user re-enters their own config on the new
per-user Settings → Assistant page (§7.1 placement, FU-153 close-out).

Revision ID: e5b9d3c7a8f2
Revises: d2f7a9c4b1e8
Create Date: 2026-06-29 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'e5b9d3c7a8f2'
down_revision = 'd2f7a9c4b1e8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('llm_enabled')
        batch.drop_column('llm_base_url')
        batch.drop_column('llm_model')
        batch.add_column(
            sa.Column(
                'master_llm_enabled',
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
        )

    with op.batch_alter_table('User') as batch:
        batch.add_column(
            sa.Column(
                'llm_enabled',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
        batch.add_column(sa.Column('llm_provider', sa.String(length=16), nullable=True))
        batch.add_column(sa.Column('llm_base_url', sa.String(length=500), nullable=True))
        batch.add_column(sa.Column('llm_model', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('llm_api_key_encrypted', sa.LargeBinary(), nullable=True))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('llm_api_key_encrypted')
        batch.drop_column('llm_model')
        batch.drop_column('llm_base_url')
        batch.drop_column('llm_provider')
        batch.drop_column('llm_enabled')

    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('master_llm_enabled')
        batch.add_column(sa.Column('llm_model', sa.String(length=255), nullable=False, server_default=''))
        batch.add_column(sa.Column('llm_base_url', sa.String(length=500), nullable=False, server_default=''))
        batch.add_column(sa.Column('llm_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
