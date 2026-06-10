"""20260611_appsetting_install_flags

C-cross Chunk 1 — install-wide feature flags (proposal §2.6).

Adds five new boolean columns to the `AppSetting` singleton row. Existing
`llm_enabled` and `scanning_enabled` stay where they are; the proposal
explicitly says to fold them in (don't duplicate).

Conservative defaults: only `meal_planning_enabled` ships True so
existing installs don't lose the meal-planning feature on first boot
after this migration runs. Every other new flag is off by default —
admins flip them in Settings → System → Features.

Revision ID: a3b8e2f4c1d7
Revises: e1f6a2b4c8d9
Create Date: 2026-06-11 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'a3b8e2f4c1d7'
down_revision = 'e1f6a2b4c8d9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(sa.Column('meal_planning_enabled', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('money_enabled', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('nutrition_enabled', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('companion_ingestion_enabled', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('deals_email_enabled', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('deals_email_enabled')
        batch_op.drop_column('companion_ingestion_enabled')
        batch_op.drop_column('nutrition_enabled')
        batch_op.drop_column('money_enabled')
        batch_op.drop_column('meal_planning_enabled')
