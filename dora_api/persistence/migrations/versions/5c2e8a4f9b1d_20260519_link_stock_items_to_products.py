"""20260519_link_stock_items_to_products

Creates the StockItemProduct m2m bridge so a stock item can track one or
more merchant products (deals, prices, alternates). CASCADE both ways so
deleting either side cleans up its links.

Revision ID: 5c2e8a4f9b1d
Revises: 4b1d9c2e7a31
Create Date: 2026-05-19 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = '5c2e8a4f9b1d'
down_revision = '4b1d9c2e7a31'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'StockItemProduct',
        sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('product_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.ForeignKeyConstraint(['stock_item_id'], ['StockItem.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['Product.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('stock_item_id', 'product_id'),
    )


def downgrade():
    op.drop_table('StockItemProduct')
