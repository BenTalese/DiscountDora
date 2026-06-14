"""20260614_drop_stock_item_preferred_product

Drop `StockItem.preferred_product_id` (+ its FK to `Product`). The
manual "preferred merchant for this stock item" annotation was a
high-friction signal nobody set in practice and only changed the
answer in one place — the stock-value-over-time report, which now
estimates from the cheapest most-recent linked-product price
instead. The two UI sort orders (stock-item detail product list,
shopping-list offer picker) degrade cleanly to `cheapest → name`;
the barcode-lookup → stock-item path was collapsed to the m2m
fallback it already had.

Batch mode so the drop works on SQLite (table rebuild) as well as
Postgres — R-005 portable data access. Downgrade restores the
column + FK (NULLABLE, no data — the values are not recoverable).

Revision ID: d2a7f4c9e6b1
Revises: e1f7b3d9a2c4
Create Date: 2026-06-14 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

revision = 'd2a7f4c9e6b1'
down_revision = 'e1f7b3d9a2c4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItem') as batch:
        batch.drop_constraint('fk_StockItem_preferred_product_id_Product', type_='foreignkey')
        batch.drop_column('preferred_product_id')


def downgrade():
    with op.batch_alter_table('StockItem') as batch:
        batch.add_column(
            sa.Column(
                'preferred_product_id',
                sqlalchemy_utils.types.uuid.UUIDType(),
                nullable=True,
            ),
        )
        batch.create_foreign_key(
            'fk_StockItem_preferred_product_id_Product',
            'Product', ['preferred_product_id'], ['id'], ondelete='SET NULL',
        )
