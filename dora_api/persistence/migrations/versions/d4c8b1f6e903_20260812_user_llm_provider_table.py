"""20260812_user_llm_provider_table

Move per-user LLM-provider *details* off the `User` row and into a new
`UserLlmProvider` child table (one row per user+provider), so a user can
configure several providers (Ollama, OpenAI, Anthropic, Gemini) and flip the
active one via `User.llm_provider` without overwriting the others.

Adds:
  UserLlmProvider
    id                 UUID PK
    user_id            UUID  NOT NULL  FK User.id ON DELETE CASCADE
    provider           VARCHAR(16) NOT NULL   (closed-set sentinel)
    base_url           VARCHAR(500) NULL
    model              VARCHAR(255) NULL
    api_key_encrypted  BLOB NULL              (Fernet ciphertext)
    verified           BOOL NOT NULL DEFAULT 0
    verified_at        DATETIME NULL
    UNIQUE(user_id, provider)

Drops from `User`: `llm_base_url`, `llm_model`, `llm_api_key_encrypted`
(kept: `llm_enabled`, `llm_provider`).

**Pre-release hard change — no data preserved:** the old flat provider config
is dropped outright (dev DBs reset via drop_all). SQLite runs in batch mode.

Revision ID: d4c8b1f6e903
Revises: a3f8c1d6e402
Create Date: 2026-08-12 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType


revision = 'd4c8b1f6e903'
down_revision = 'a3f8c1d6e402'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'UserLlmProvider',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('user_id', UUIDType, sa.ForeignKey('User.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(length=16), nullable=False),
        sa.Column('base_url', sa.String(length=500), nullable=True),
        sa.Column('model', sa.String(length=255), nullable=True),
        sa.Column('api_key_encrypted', sa.LargeBinary(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('user_id', 'provider', name='uq_user_llm_provider_user_provider'),
    )

    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('llm_base_url')
        batch_op.drop_column('llm_model')
        batch_op.drop_column('llm_api_key_encrypted')


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column('llm_base_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('llm_model', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('llm_api_key_encrypted', sa.LargeBinary(), nullable=True))

    op.drop_table('UserLlmProvider')
