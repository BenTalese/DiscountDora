"""20260610_user_voice_prefs

P2-13 — add `voice_input_enabled` and `voice_output_enabled` to the User
table so a user's voice opt-in survives across sessions. Both default to
False — voice is browser-API-dependent and opt-in, never an automatic
behaviour.

Revision ID: e7c4b8a1d2f9
Revises: d3a5e8c1f9b2
Create Date: 2026-06-10 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'e7c4b8a1d2f9'
down_revision = 'd3a5e8c1f9b2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'voice_input_enabled', sa.Boolean(),
            nullable=False, server_default='0',
        ))
        batch.add_column(sa.Column(
            'voice_output_enabled', sa.Boolean(),
            nullable=False, server_default='0',
        ))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('voice_output_enabled')
        batch.drop_column('voice_input_enabled')
