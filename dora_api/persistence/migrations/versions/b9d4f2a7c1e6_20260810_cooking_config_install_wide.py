"""20260810_cooking_config_install_wide

FU-615 — move the two household cooking prefs off `User` and onto the
install-wide `AppSetting` singleton:

  * `household_headcount` (nullable int) — how many people the household
    cooks for; cook mode seeds its serving scaler from it.
  * `batch_features_enabled` (bool, default False) — the household cook-style
    ("batch" reveals the meal-planner cook pool + shortfall warning).

Both were put on `User` only as a convenient home for cook-mode's scaler
(PROPOSAL_ONBOARDING §3.4); a household has one headcount and one cook-style,
so they belong install-wide. **Pre-release hard change — no data preserved:**
the `User` columns are dropped outright (any values they held are discarded),
and the new `AppSetting` columns start at their seeded defaults (no headcount,
fresh cook-style). SQLite runs both in batch mode (table recreate).

Revision ID: b9d4f2a7c1e6
Revises: f4a2c7e9b1d3
Create Date: 2026-08-10 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'b9d4f2a7c1e6'
down_revision = 'f4a2c7e9b1d3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(sa.Column('household_headcount', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column(
            'batch_features_enabled', sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ))
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('household_headcount')
        batch_op.drop_column('batch_features_enabled')


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column('household_headcount', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column(
            'batch_features_enabled', sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ))
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('batch_features_enabled')
        batch_op.drop_column('household_headcount')
