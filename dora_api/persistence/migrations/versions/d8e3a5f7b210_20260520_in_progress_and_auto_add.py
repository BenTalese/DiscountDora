"""20260520_in_progress_and_auto_add

Two small additions:

  ShoppingList.is_in_progress  — "I'm actively shopping right now" flag
  StockItem.auto_add_when_low  — when an item drops to Low or Out, auto-add
                                 it to the primary shopping list

Both default to False so existing rows pick up safe values without a
backfill.

Revision ID: d8e3a5f7b210
Revises: c4f7a2b8e1d6
Create Date: 2026-05-20 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd8e3a5f7b210'
down_revision = 'c4f7a2b8e1d6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingList') as batch:
        batch.add_column(sa.Column(
            'is_in_progress', sa.Boolean(), nullable=False, server_default=sa.text('0')
        ))
    with op.batch_alter_table('StockItem') as batch:
        batch.add_column(sa.Column(
            'auto_add_when_low', sa.Boolean(), nullable=False, server_default=sa.text('0')
        ))


def downgrade():
    with op.batch_alter_table('StockItem') as batch:
        batch.drop_column('auto_add_when_low')
    with op.batch_alter_table('ShoppingList') as batch:
        batch.drop_column('is_in_progress')
