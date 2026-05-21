"""20260520_app_settings

Adds the install-wide AppSetting table (a single row, get-or-created in code).
Currently holds the opt-in, bring-your-own-LLM assistant config:

  AppSetting.llm_enabled   — boolean, default False
  AppSetting.llm_base_url  — text, default '' (e.g. http://localhost:11434)
  AppSetting.llm_model     — text, default '' (e.g. qwen2.5:7b)

Nothing is enabled by default; an admin turns it on in Settings.

Revision ID: f1a2b3c4d5e6
Revises: e9c2b748f015
Create Date: 2026-05-20 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e9c2b748f015'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'AppSetting',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('llm_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('llm_base_url', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('llm_model', sa.String(length=255), nullable=False, server_default=''),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('AppSetting')
