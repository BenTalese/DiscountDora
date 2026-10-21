"""20260603_price_alerts

Adds the PriceAlert table — per-user subscriptions that fire (via the
existing notification path) when a future scrape sees a product's
unit_price drop to or below the user's threshold.

Revision ID: d3b6e1f9a720
Revises: c8a1d3b6e9f4
Create Date: 2026-06-03 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

# revision identifiers, used by Alembic.
revision = 'd3b6e1f9a720'
down_revision = 'c8a1d3b6e9f4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'PriceAlert',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('user_id', UUIDType, sa.ForeignKey('User.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', UUIDType, sa.ForeignKey('Product.id', ondelete='CASCADE'), nullable=False),
        sa.Column('threshold_unit_price', sa.Float, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_fired_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_PriceAlert_user_product', 'PriceAlert', ['user_id', 'product_id'])
    op.create_index('ix_PriceAlert_product', 'PriceAlert', ['product_id'])


def downgrade():
    op.drop_index('ix_PriceAlert_product', table_name='PriceAlert')
    op.drop_index('ix_PriceAlert_user_product', table_name='PriceAlert')
    op.drop_table('PriceAlert')
