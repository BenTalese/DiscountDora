"""20260819_buy_verdict_per_user

D-12 (`docs/04_proposals/IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`) — move
`buy_verdict_enabled` from `AppSetting` (household) to `User` (per-user).

It was scoped to the household for a setting that only changes what *one*
person sees: the "should I buy this?" card and badge are a display overlay on
top of Dora's own reasoning, with no shared writes behind them. So one member
turning the badge off turned it off for everyone (B7 — owner confirmed the
original scoping was a mistake). It now sits beside `inferred_pantry_enabled`,
the other "one of Dora's opinions you may not want to read" toggle.

The rule this established, and the reason it's worth a migration rather than a
shrug: **a setting that mutates shared state is household-scoped; a setting
that only changes what you see is per-user.**

Clean move, no backfill shim (pre-release, per the standing migrations policy):
the old column is dropped and the new one defaults to True, which is what the
old column defaulted to. An install that had switched the verdict off
household-wide gets it back on for everyone — acceptable for a badge, and the
alternative (a per-user backfill from a household row) would be inventing
individual preferences nobody expressed.

Revision ID: d9f4b2c7e803
Revises: f2a9c4e18b73
Create Date: 2026-08-19 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import true

revision = 'd9f4b2c7e803'
down_revision = 'f2a9c4e18b73'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column(
            'buy_verdict_enabled', sa.Boolean(), nullable=False,
            server_default=true(),
        ))
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('buy_verdict_enabled')


def downgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(sa.Column(
            'buy_verdict_enabled', sa.Boolean(), nullable=False,
            server_default=true(),
        ))
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('buy_verdict_enabled')
