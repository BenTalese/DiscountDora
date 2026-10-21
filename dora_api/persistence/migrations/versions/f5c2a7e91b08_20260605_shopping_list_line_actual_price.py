"""20260605_shopping_list_line_actual_price

P2-02 — adds ShoppingListLine.actual_unit_price + purchased_merchant_id so
users can record what they *actually* paid and where they actually bought
an item, distinct from the planned offer snapshot
(picked_offer_price / selected_product_id).

Both columns are NULL by default — the existing picked_offer_price stays
the historic source-of-truth when the shopper didn't override. The
assistant's purchase-price stats tool prefers actual_unit_price when set,
otherwise falls back to picked_offer_price.

Revision ID: f5c2a7e91b08
Revises: e4f9c2a18d3b
Create Date: 2026-06-05 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'f5c2a7e91b08'
down_revision = 'e4f9c2a18d3b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingListLine') as batch:
        batch.add_column(sa.Column('actual_unit_price', sa.Float(), nullable=True))
        batch.add_column(sa.Column('purchased_merchant_id', UUIDType, nullable=True))
        batch.create_foreign_key(
            'fk_shoppinglistline_purchased_merchant',
            'Merchant',
            ['purchased_merchant_id'], ['id'],
            ondelete='SET NULL',
        )


def downgrade():
    with op.batch_alter_table('ShoppingListLine') as batch:
        batch.drop_constraint('fk_shoppinglistline_purchased_merchant', type_='foreignkey')
        batch.drop_column('purchased_merchant_id')
        batch.drop_column('actual_unit_price')
