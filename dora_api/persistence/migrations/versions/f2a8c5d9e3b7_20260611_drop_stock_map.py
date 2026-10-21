"""20260611_drop_stock_map

Drop the StockMap table — the hand-drawn pantry layout page has been
removed from the product. The table was single-row JSON storage with
no foreign-key fan-out, so nothing else depends on it.

Revision ID: f2a8c5d9e3b7
Revises: e7c4b8a1d2f9
Create Date: 2026-06-11 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'f2a8c5d9e3b7'
down_revision = 'e7c4b8a1d2f9'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('StockMap')


def downgrade():
    op.create_table(
        'StockMap',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('layout', sa.Text, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
