"""20260529_stocktake_last_checked

Adds StockItem.last_checked_at — the timestamp of the most recent
"I confirmed this level is still correct" event, separate from
stock_level_last_updated which only moves when the level itself changes.

X1's stocktake mode queries off this column; index on it for the
oldest-first ordering used by /api/stocktake/queue.

Revision ID: a4c7e1d9b832
Revises: f3b1c8e7d2a9
Create Date: 2026-05-29 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a4c7e1d9b832'
down_revision = 'f3b1c8e7d2a9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItem') as batch:
        batch.add_column(sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_StockItem_last_checked_at', 'StockItem', ['last_checked_at'])


def downgrade():
    op.drop_index('ix_StockItem_last_checked_at', table_name='StockItem')
    with op.batch_alter_table('StockItem') as batch:
        batch.drop_column('last_checked_at')
