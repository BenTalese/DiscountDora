"""20260520_stock_open_marker

Adds the "I've cracked it open" tracking to StockItem:

  StockItem.is_open    — boolean, default False
  StockItem.opened_on  — nullable date, set when is_open flips on

StockGroup already exists as an entity + table; this migration doesn't
need to create it. The CRUD endpoints + UI for groups land in this round
but the schema is unchanged.

Revision ID: e9c2b748f015
Revises: d8e3a5f7b210
Create Date: 2026-05-20 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e9c2b748f015'
down_revision = 'd8e3a5f7b210'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItem') as batch:
        batch.add_column(sa.Column(
            'is_open', sa.Boolean(), nullable=False, server_default=sa.false()
        ))
        batch.add_column(sa.Column('opened_on', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('StockItem') as batch:
        batch.drop_column('opened_on')
        batch.drop_column('is_open')
