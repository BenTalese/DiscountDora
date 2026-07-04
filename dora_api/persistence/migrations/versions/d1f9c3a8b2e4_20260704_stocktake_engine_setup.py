"""20260704_stocktake_engine_setup

Chunk 1 of the stocktake-mode redesign
(``docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md``). Three coupled schema
changes shipped in one revision because Chunk 1 flips the whole queue
engine over at once — half the columns would leave the runtime in an
inconsistent state.

Also serves as the **merge migration** between the two open heads
(``a3e8b1f6c2d9`` user_inferred_pantry + ``c5a8e1f7d3b2``
recipe_ingredient_unlinked) — both mid-week concurrent work, both head
as of the FU-226/FU-430 Chunk-1 start.

Changes:

1. ``StockItem.snoozed_until`` (nullable ``DateTime(timezone=True)``).
   Backs the "Push 3 days" resolution verb — the queue filter excludes
   items whose ``snoozed_until > now``. Indexed so the queue's
   ``WHERE snoozed_until IS NULL OR snoozed_until <= NOW()`` stays cheap
   on a big pantry.

2. ``AppSetting.stocktake_default_cadence_band`` (``String(16)``,
   default ``'fortnightly'``). Global default check cadence when the
   Auto self-tuner is off, and the baseline Auto starts from for
   never-touched items. Values: ``'weekly' | 'fortnightly' | 'monthly'``.

3. ``AppSetting.stocktake_auto_tuning_enabled`` (Boolean, default
   ``true``). Master switch for the movement-history self-tuner —
   "auto = speed" per the user's design call. Existing installs adopt
   Auto-on-by-default on upgrade; users can opt back to a flat global
   default from Settings → Stocktake (Chunk 3).

The pre-existing per-item ``days_until_stocktake_alert`` column is
**not** dropped by this migration — it's superseded by the band system
(§7 of the brief) but left in place so old writers don't error mid-
transition. Drop is deferred until Chunk 2's SPA cutover lands.

Revision ID: d1f9c3a8b2e4
Revises: a3e8b1f6c2d9, c5a8e1f7d3b2
Create Date: 2026-07-04 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import true


revision = 'd1f9c3a8b2e4'
down_revision = ('a3e8b1f6c2d9', 'c5a8e1f7d3b2')
branch_labels = None
depends_on = None


_DEFAULT_CADENCE_BAND = 'fortnightly'


def upgrade():
    # StockItem.snoozed_until — R-005 batch_alter_table so SQLite recreates
    # the table cleanly. Nullable + no server_default; NULL means "not
    # snoozed", which is the correct state for every existing row.
    with op.batch_alter_table('StockItem') as batch:
        batch.add_column(sa.Column(
            'snoozed_until', sa.DateTime(timezone=True), nullable=True,
        ))
    op.create_index(
        'ix_StockItem_snoozed_until', 'StockItem', ['snoozed_until'],
    )

    # AppSetting — two new columns with sensible install-wide defaults.
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'stocktake_default_cadence_band', sa.String(16),
            nullable=False, server_default=_DEFAULT_CADENCE_BAND,
        ))
        batch.add_column(sa.Column(
            'stocktake_auto_tuning_enabled', sa.Boolean(),
            nullable=False, server_default=true(),
        ))


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('stocktake_auto_tuning_enabled')
        batch.drop_column('stocktake_default_cadence_band')

    op.drop_index('ix_StockItem_snoozed_until', table_name='StockItem')
    with op.batch_alter_table('StockItem') as batch:
        batch.drop_column('snoozed_until')
