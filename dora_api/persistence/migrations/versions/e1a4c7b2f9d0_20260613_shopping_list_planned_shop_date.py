"""20260613_shopping_list_planned_shop_date

P6-01 Chunk 7. Adds an optional `planned_shop_date` (DATE) to ShoppingList so
the landing page can prefer "today's list" and the selector can sort by it.
Nullable — most existing rows won't have one, and the absence reads as
"unscheduled".

Batch mode for SQLite portability (R-005).

Revision ID: e1a4c7b2f9d0
Revises: d5e9f3b2a1c8
Create Date: 2026-06-13 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'e1a4c7b2f9d0'
down_revision = 'd5e9f3b2a1c8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingList') as batch:
        batch.add_column(sa.Column('planned_shop_date', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('ShoppingList') as batch:
        batch.drop_column('planned_shop_date')
