"""20260617_stock_item_price_observation

FU-213 (PROPOSAL_PRODUCTS_AS_OVERLAY §3.2) — `StockItemPriceObservation`: the
everyday "what this cost me" price substrate on a stock item (total price + qty
+ unit + observed_at + source). Per-unit cost is derived server-side. No
merchant attribution in the everyday layer. CASCADE-deleted with the stock item.

Revision ID: b3d5f7a9c2e4
Revises: a2c4e6f8b1d3
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

revision = 'b3d5f7a9c2e4'
down_revision = 'a2c4e6f8b1d3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'StockItemPriceObservation',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['stock_item_id'], ['StockItem.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('StockItemPriceObservation')
