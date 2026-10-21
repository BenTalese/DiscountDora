"""20260607_stock_item_waste_events

P2-06 — append-only log of food the user discarded. Optional capture
(one-tap "I had to throw this out" on the Waste page); feeds Dora's
`waste_insights` tool and the waste history strip on StockItemDetail.

The FK to StockItem is `SET NULL` rather than `CASCADE` so deleting a
stock item doesn't erase its waste history — the denormalised
`stock_item_name` column on each row keeps the insights readable.

Revision ID: b8d4e1c7a2f3
Revises: a6e3b5d2c8f1
Create Date: 2026-06-07 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'b8d4e1c7a2f3'
down_revision = 'a6e3b5d2c8f1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'StockItemWasteEvent',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column(
            'stock_item_id', UUIDType,
            sa.ForeignKey('StockItem.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('stock_item_name', sa.String(length=255), nullable=False),
        sa.Column('reason', sa.String(length=32), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('estimated_value', sa.Float(), nullable=True),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table('StockItemWasteEvent')
