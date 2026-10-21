"""20261021_recipe_ingredient_choice

Lets a recipe ingredient say which one of its stock item it means: a name of
its own (`label`), one of the item's preferred buys (`preferred_buy_id`), or a
linked product (`selected_product_id`). Mirrors the shopping line's choice
columns; `preferred_buy_id` is a plain UUID with no FK, matching it.

Revision ID: f2a6c8e1b4d7
Revises: e4b7c2a9f1d3
Create Date: 2026-10-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


revision = 'f2a6c8e1b4d7'
down_revision = 'e4b7c2a9f1d3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('RecipeIngredient') as batch:
        batch.add_column(sa.Column('label', sa.String(255), nullable=True))
        batch.add_column(sa.Column(
            'preferred_buy_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True,
        ))
        batch.add_column(sa.Column(
            'selected_product_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True,
        ))
        batch.create_foreign_key(
            'fk_RecipeIngredient_selected_product_id_Product',
            'Product', ['selected_product_id'], ['id'], ondelete='SET NULL',
        )
        batch.create_index(
            'ix_RecipeIngredient_selected_product_id', ['selected_product_id'],
        )


def downgrade():
    with op.batch_alter_table('RecipeIngredient') as batch:
        batch.drop_index('ix_RecipeIngredient_selected_product_id')
        batch.drop_constraint(
            'fk_RecipeIngredient_selected_product_id_Product', type_='foreignkey',
        )
        batch.drop_column('selected_product_id')
        batch.drop_column('preferred_buy_id')
        batch.drop_column('label')
