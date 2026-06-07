"""20260612_drop_stock_item_barcode

P6-02 barcode model correction. A real-world barcode (EAN/UPC) identifies a
*Product* (a SKU), not a stock item — a stock item can map to many products /
barcodes. So the single `StockItem.barcode` column was the wrong model and is
dropped here; `ProductBarcode` (barcode → Product) is the correct model and is
kept untouched.

Also adds the install-wide `scanning_enabled` flag to AppSetting — one
off-by-default switch gating the whole scanning + QR-labels surface.

Batch mode so the column drop works on SQLite (which rebuilds the table) as
well as Postgres — R-005 portable data access.

Revision ID: a3f1c7d2e9b4
Revises: b2c3d4e5f6a7
Create Date: 2026-06-12 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'a3f1c7d2e9b4'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItem') as batch:
        batch.drop_constraint('uq_StockItem_barcode', type_='unique')
        batch.drop_column('barcode')

    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'scanning_enabled', sa.Boolean(),
            nullable=False, server_default='0',
        ))


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('scanning_enabled')

    with op.batch_alter_table('StockItem') as batch:
        batch.add_column(sa.Column('barcode', sa.String(255), nullable=True))
        batch.create_unique_constraint('uq_StockItem_barcode', ['barcode'])
