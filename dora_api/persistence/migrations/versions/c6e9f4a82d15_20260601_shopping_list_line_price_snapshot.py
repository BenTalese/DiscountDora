"""20260601_shopping_list_line_price_snapshot

Adds ShoppingListLine.picked_offer_price + list_price_at_pick — a frozen
copy of the chosen merchant offer at the moment the line is ticked off.

The reporting endpoints (N6) need these to answer "how much did I save vs
RRP on archived lists" honestly. Computing the answer at read time from the
*current* offer price lies after a future price move; snapshotting locks
the answer in.

Captured by the line-update path when `is_ticked` flips True (and the line
has a `selected_product_id` resolvable to a current offer). Lines never
ticked leave both columns NULL; the reports just skip them.

Revision ID: c6e9f4a82d15
Revises: b5d8e2f3c14a
Create Date: 2026-06-01 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'c6e9f4a82d15'
down_revision = 'b5d8e2f3c14a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingListLine') as batch:
        batch.add_column(sa.Column('picked_offer_price', sa.Float(), nullable=True))
        batch.add_column(sa.Column('list_price_at_pick', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('ShoppingListLine') as batch:
        batch.drop_column('list_price_at_pick')
        batch.drop_column('picked_offer_price')
