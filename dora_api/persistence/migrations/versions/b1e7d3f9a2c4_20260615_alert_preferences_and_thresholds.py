"""20260615_alert_preferences_and_thresholds

C-9.2 — per-user alert preferences (enable/disable + tier override per kind)
plus household-wide alert thresholds on AppSetting (the expiring-soon window +
the default stocktake timeframe). The expiring-soon window moves off the
hardcoded `EXPIRING_SOON_WINDOW_DAYS` constant onto AppSetting; the constant
becomes the seeded default (R-003 — one source preserved).

A fresh table + plain ADD COLUMN with constant `server_default`s need no table
rebuild, so this applies natively on SQLite and Postgres alike — no
`batch_alter_table` recreation, so it is independent of the batch-mode
constraint-naming issue that breaks a full-chain SQLite `upgrade`
(DORA_FOLLOWUPS FU-178). Reversible (R-006); portable (R-005, §7.5).

Revision ID: b1e7d3f9a2c4
Revises: f4d2a9c7b3e1
Create Date: 2026-06-15 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'b1e7d3f9a2c4'
down_revision = 'f4d2a9c7b3e1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'AlertPreference',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('user_id', UUIDType, nullable=False),
        sa.Column('kind', sa.String(length=64), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('tier_override', sa.String(length=16), nullable=True),
    )
    # One pref row per (user, kind); the unique index also serves the hot
    # "this user's prefs" lookup in the GET /alerts overlay.
    op.create_index(
        'ix_alert_preference_user_kind',
        'AlertPreference',
        ['user_id', 'kind'],
        unique=True,
    )
    # Household-wide alert thresholds (PROPOSAL_ALERTS §3.3 / §4.4). Constant
    # server_defaults preserve today's behaviour exactly: the 7-day window is
    # the former EXPIRING_SOON_WINDOW_DAYS constant; 0 = no default stocktake
    # cadence on new items (unchanged from the previously-hardcoded create path).
    op.add_column('AppSetting', sa.Column(
        'expiring_soon_window_days', sa.Integer(), nullable=False, server_default='7'))
    op.add_column('AppSetting', sa.Column(
        'default_days_until_stocktake_alert', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('AppSetting', 'default_days_until_stocktake_alert')
    op.drop_column('AppSetting', 'expiring_soon_window_days')
    op.drop_index('ix_alert_preference_user_kind', table_name='AlertPreference')
    op.drop_table('AlertPreference')
