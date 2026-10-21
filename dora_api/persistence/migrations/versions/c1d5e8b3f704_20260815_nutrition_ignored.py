"""20260815_nutrition_ignored

Owner call 2026-08-15 — nutrition gets an auto-suggestion path, so it needs an
opt-out.

Complex mode previously required the user to open a picker and search for every
single stock item before any nutrition number existed. The suggester now offers
a best local-catalogue match per unlinked item; accepting one writes the same
explicit `nutrition_food_id` link it always did.

That makes "no link" ambiguous — it could mean "not got round to it" or "this is
toilet paper". `nutrition_ignored` disambiguates: an item the user has waved off
leaves the unmatched queue for good, instead of being re-suggested forever.
Nothing else reads it, so no data migration is needed — every existing item
starts as "still worth asking".

Revision ID: c1d5e8b3f704
Revises: b9e3f1a7c4d2
Create Date: 2026-08-15 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'c1d5e8b3f704'
down_revision = 'b9e3f1a7c4d2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItem') as batch_op:
        batch_op.add_column(sa.Column(
            'nutrition_ignored', sa.Boolean(), nullable=False, server_default=sa.false(),
        ))
    op.create_index('ix_StockItem_nutrition_ignored', 'StockItem', ['nutrition_ignored'])


def downgrade():
    op.drop_index('ix_StockItem_nutrition_ignored', table_name='StockItem')
    with op.batch_alter_table('StockItem') as batch_op:
        batch_op.drop_column('nutrition_ignored')
