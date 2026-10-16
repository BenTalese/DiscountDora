"""20261014_template_line_choice

Gives `ShoppingListTemplateLine` the same "which one" choice a shopping-list
line carries: a picked offer (`selected_product_id`) and a preferred buy
(`preferred_buy_id`). The template editor now offers the list row's picker, and
instantiating a template copies both onto the new list.

`preferred_buy_id` is a plain UUID with no FK, matching `ShoppingListLine`.

Revision ID: c3e8a5f1d7b4
Revises: a1c7e4b9d2f6
Create Date: 2026-10-14 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


revision = 'c3e8a5f1d7b4'
down_revision = 'a1c7e4b9d2f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingListTemplateLine') as batch:
        batch.add_column(sa.Column(
            'selected_product_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True,
        ))
        batch.add_column(sa.Column(
            'preferred_buy_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True,
        ))
        batch.create_foreign_key(
            'fk_ShoppingListTemplateLine_selected_product_id_Product',
            'Product', ['selected_product_id'], ['id'], ondelete='SET NULL',
        )
        batch.create_index(
            'ix_ShoppingListTemplateLine_selected_product_id', ['selected_product_id'],
        )


def downgrade():
    with op.batch_alter_table('ShoppingListTemplateLine') as batch:
        batch.drop_index('ix_ShoppingListTemplateLine_selected_product_id')
        batch.drop_constraint(
            'fk_ShoppingListTemplateLine_selected_product_id_Product', type_='foreignkey',
        )
        batch.drop_column('preferred_buy_id')
        batch.drop_column('selected_product_id')
