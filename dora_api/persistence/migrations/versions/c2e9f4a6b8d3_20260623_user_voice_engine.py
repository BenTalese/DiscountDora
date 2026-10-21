"""20260623_user_voice_engine

Add `voice_engine` and `voice_id` to the User table so a user's choice of
speech engine (browser vs. Piper neural voice) and which Piper voice survives
across sessions. Defaults `piper` / `amy`: Dora uses the bundled neural voice
when it's available, falling back to the browser voice client-side otherwise.
These only take effect when `voice_output_enabled` is on.

Revision ID: c2e9f4a6b8d3
Revises: a4f7c2e9b6d1
Create Date: 2026-06-23 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'c2e9f4a6b8d3'
down_revision = 'a4f7c2e9b6d1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'voice_engine', sa.String(length=16),
            nullable=False, server_default='piper',
        ))
        batch.add_column(sa.Column(
            'voice_id', sa.String(length=32),
            nullable=False, server_default='amy',
        ))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('voice_id')
        batch.drop_column('voice_engine')
