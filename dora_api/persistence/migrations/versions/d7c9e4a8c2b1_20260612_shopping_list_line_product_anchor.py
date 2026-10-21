"""20260612_shopping_list_line_product_anchor

C-7 Chunk 3 — standalone-product shopping-list lines. A line is now
anchored by `stock_item_id` OR `product_id`, with both nullable
individually; a CHECK enforces "at least one set". This unblocks the
"add a product whose linked stock item isn't on the list" path
(L130 / L191) and the nested display on the list detail.

Pre-release semantics: existing dev/test rows are recreated cleanly —
no data migration. SQLite-friendly: batch-mode for both the nullable
flip and the new column + CHECK + FK.

Revision ID: d7c9e4a8c2b1
Revises: f6c8e3a9b1d2
Create Date: 2026-06-12 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'd7c9e4a8c2b1'
down_revision = 'f6c8e3a9b1d2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingListLine') as batch_op:
        # Flip stock_item_id to nullable.
        batch_op.alter_column(
            'stock_item_id',
            existing_type=UUIDType(),
            nullable=True,
        )
        # New product anchor. ON DELETE CASCADE so a deleted product
        # never leaves an orphan line; the entity-level rule 4 modal
        # ("also remove the stock item?") is UX, not data integrity.
        batch_op.add_column(
            sa.Column(
                'product_id', UUIDType(),
                sa.ForeignKey('Product.id', ondelete='CASCADE'),
                nullable=True,
            ),
        )
        # At least one of the two anchors must be set. Catches bad
        # writes at the DB layer; the handler also validates upstream
        # so the SPA gets a clean 400 instead of a 500.
        batch_op.create_check_constraint(
            'ck_shopping_list_line_anchor',
            'stock_item_id IS NOT NULL OR product_id IS NOT NULL',
        )


def downgrade():
    with op.batch_alter_table('ShoppingListLine') as batch_op:
        batch_op.drop_constraint('ck_shopping_list_line_anchor', type_='check')
        batch_op.drop_column('product_id')
        batch_op.alter_column(
            'stock_item_id',
            existing_type=UUIDType(),
            nullable=False,
        )
