"""20260614_app_setting_timezone

Meal Plans C-2.K — household IANA timezone on AppSetting. The "today" date
boundary (meal-plan past-day rules + the reconcile sweep) is evaluated in this
timezone so a household is correct regardless of where the server is hosted.
Defaults to UTC; an admin sets it in System settings.

A constant `server_default` needs no table rebuild, so a plain ADD COLUMN
applies natively on SQLite and Postgres alike (R-005) — no `batch_alter_table`
recreation, so this is independent of the batch-mode constraint-naming issue
that breaks a full-chain SQLite `upgrade` (DORA_FOLLOWUPS FU-178).
Reversible (R-006).

Revision ID: c3a7e1f9d4b6
Revises: b9f6d3a8c1e2
Create Date: 2026-06-14 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'c3a7e1f9d4b6'
down_revision = 'b9f6d3a8c1e2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'AppSetting',
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='UTC'),
    )


def downgrade():
    op.drop_column('AppSetting', 'timezone')
