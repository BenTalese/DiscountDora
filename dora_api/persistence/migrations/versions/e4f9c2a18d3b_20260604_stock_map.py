"""20260604_stock_map

Single-row StockMap table — JSON blob holding the user's hand-drawn
pantry layout (rectangles, colours, sizes per location). The schema
isn't user-scoped today; one map per install matches the rest of the
codebase.

Revision ID: e4f9c2a18d3b
Revises: d3b6e1f9a720
Create Date: 2026-06-04 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

# revision identifiers, used by Alembic.
revision = 'e4f9c2a18d3b'
down_revision = 'd3b6e1f9a720'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'StockMap',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('layout', sa.Text, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table('StockMap')
