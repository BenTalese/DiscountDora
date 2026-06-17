"""20260617_preferred_buys

FU-211 (PROPOSAL_PRODUCTS_AS_OVERLAY §3.1) — `PreferredBuy`: free-text "what I
actually buy" reminders attached to a stock item (the everyday counterpart to
the power-user Product overlay). Owned child rows, ordered by `position`,
CASCADE-deleted with their stock item.

Revision ID: a2c4e6f8b1d3
Revises: f1a2b3c4d5e6
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

revision = 'a2c4e6f8b1d3'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'PreferredBuy',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['stock_item_id'], ['StockItem.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('PreferredBuy')
