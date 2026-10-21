"""20260704_drop_deprecated_stocktake_days

Housekeeping cleanup for the stocktake-mode redesign
(``docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md``). Drops two columns
that the redesign made obsolete:

1. ``StockItem.days_until_stocktake_alert`` — the per-item cadence
   dial. Superseded by the band system (weekly / fortnightly /
   monthly), resolved server-side from the global default +
   Essential + Auto self-tuning + Low/Out bump. See
   ``dora_api/features/stocktake/cadence.py``.

2. ``AppSetting.default_days_until_stocktake_alert`` — the household
   default used to seed the per-item field on create. No longer
   consulted by anything after Chunks 1–3 landed; the settings UI
   surface it powered was removed in Chunk 3.

Also finishes retiring the dead ``locations/attention.py`` heatmap
system (the ``stocktake_overdue`` reason lived there); alerts +
heatmap were both rewired to the queue's ``resolve_overdue_map``
authority in the same cleanup pass. No schema change here for the
heatmap — it was pure runtime code.

Revision ID: e5c8b3a1f4d2
Revises: d1f9c3a8b2e4
Create Date: 2026-07-04 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'e5c8b3a1f4d2'
down_revision = 'd1f9c3a8b2e4'
branch_labels = None
depends_on = None


def upgrade():
    # R-005 — batch_alter_table so SQLite recreates the table cleanly.
    with op.batch_alter_table('StockItem') as batch:
        batch.drop_column('days_until_stocktake_alert')
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('default_days_until_stocktake_alert')


def downgrade():
    # Symmetrical rehydrate. The historical default on both columns was
    # 0 (= "no per-item stocktake alert configured"); use it so an
    # existing pantry doesn't get spurious alerts on downgrade. New
    # rows written after upgrade won't have anything to backfill.
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'default_days_until_stocktake_alert', sa.Integer(),
            nullable=False, server_default='0',
        ))
    with op.batch_alter_table('StockItem') as batch:
        batch.add_column(sa.Column(
            'days_until_stocktake_alert', sa.Integer(),
            nullable=True,
        ))
