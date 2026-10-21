"""20260630_stock_item_expiry_event

Append-only log of "the user set / pushed / cleared this item's
expiry date." Written by every StockItem handler that mutates
`expiry_date` (create_stock_item.py + update_stock_item.py — the
row-menu +N-day nudges and the row-menu Clear expiry both PATCH the
same endpoint, so both flow through this single emit site).

Consumed by the Stock Item detail's History tab. Highest signal on
perishables where a pattern of repeat pushes tells the user
something.

FK to StockItem is `SET NULL` so deleting the item doesn't wipe the
expiry-change trail (mirrors the WasteEvent policy).

Revision ID: d4e8f2b1c9a5
Revises: c3d7f1a2b8e4
Create Date: 2026-06-30 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'd4e8f2b1c9a5'
down_revision = 'c3d7f1a2b8e4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'StockItemExpiryEvent',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column(
            'stock_item_id', UUIDType,
            sa.ForeignKey('StockItem.id', ondelete='SET NULL'),
            nullable=True,
        ),
        # Small enum, plain varchar — matches WasteEvent.reason.
        sa.Column('kind', sa.String(length=16), nullable=False),
        sa.Column('previous_expiry_date', sa.Date(), nullable=True),
        sa.Column('new_expiry_date', sa.Date(), nullable=True),
        # Only populated on `pushed` events. Null on set / cleared.
        sa.Column('delta_days', sa.Integer(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    )
    # The detail projection scans by stock_item_id and sorts by
    # occurred_at; index the FK so the seek is cheap on chatty items.
    op.create_index(
        'stock_item_expiry_event_stock_item_id',
        'StockItemExpiryEvent', ['stock_item_id'],
    )


def downgrade():
    op.drop_index(
        'stock_item_expiry_event_stock_item_id',
        table_name='StockItemExpiryEvent',
    )
    op.drop_table('StockItemExpiryEvent')
