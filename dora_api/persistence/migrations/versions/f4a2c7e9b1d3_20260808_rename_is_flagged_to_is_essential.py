"""20260808_rename_is_flagged_to_is_essential

Rename `StockItem.is_flagged` → `StockItem.is_essential`. The column has
always *meant* "this item is essential" (the auto-add and stocktake-cadence
resolvers read it as the Essential signal, the UI filter is "Essentials",
the import mapping targets `is_essential`), but the physical column kept the
legacy `is_flagged` name. This aligns the schema with the domain term so
there's a single name — `is_essential` — across code and database.

Boolean column, NOT NULL, `server_default=false()`; no data transform, just
a name change. SQLite runs it in batch mode (table recreate).

Revision ID: f4a2c7e9b1d3
Revises: d3f8b1a6c4e2
Create Date: 2026-08-08 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'f4a2c7e9b1d3'
down_revision = 'd3f8b1a6c4e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItem') as batch_op:
        batch_op.alter_column(
            'is_flagged', new_column_name='is_essential',
            existing_type=sa.Boolean(),
            existing_nullable=False,
            existing_server_default=sa.false(),
        )


def downgrade():
    with op.batch_alter_table('StockItem') as batch_op:
        batch_op.alter_column(
            'is_essential', new_column_name='is_flagged',
            existing_type=sa.Boolean(),
            existing_nullable=False,
            existing_server_default=sa.false(),
        )
