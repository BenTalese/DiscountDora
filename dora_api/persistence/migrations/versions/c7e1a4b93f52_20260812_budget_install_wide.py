"""20260812_budget_install_wide

Move the grocery budget off `User` and onto the install-wide `AppSetting`
singleton, and drop the per-user money opt-in entirely.

  * `AppSetting.budget_amount` (nullable float) — the household grocery
    budget; NULL/≤0 ⇒ off (value-driven, no separate enabled flag).
  * `AppSetting.budget_period` (string, default 'weekly') — rolling window.

Budget "spent" is summed across every *shared* shopping list in the period
(the schema is single-household), so the target has to be shared too — a
per-user budget compared against a household spend total is incoherent. Same
class of fix as FU-615 (`household_headcount` / `batch_features_enabled`).

The per-user `money_features_enabled` opt-in is removed: money is one
install-wide concern now (`AppSetting.money_enabled`). If the install has
money on, dollar surfaces render for everyone; off hides them for everyone.

**Pre-release hard change — no data preserved:** the three `User` columns are
dropped outright (any values discarded) and the new `AppSetting` columns start
at their seeded defaults (no budget, weekly). SQLite runs in batch mode.

Revision ID: c7e1a4b93f52
Revises: d5a9f27c4e18
Create Date: 2026-08-12 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'c7e1a4b93f52'
down_revision = 'd5a9f27c4e18'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(sa.Column('budget_amount', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column(
            'budget_period', sa.String(length=16),
            nullable=False, server_default='weekly',
        ))
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('budget_amount')
        batch_op.drop_column('budget_period')
        batch_op.drop_column('money_features_enabled')


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column('budget_amount', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column(
            'budget_period', sa.String(length=16),
            nullable=False, server_default='weekly',
        ))
        batch_op.add_column(sa.Column(
            'money_features_enabled', sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ))
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('budget_period')
        batch_op.drop_column('budget_amount')
