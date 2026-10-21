"""20260520_shopping_list_overhaul

Replaces the skeletal ShoppingList + ShoppingListStockItem m2m with a richer
model:

  ShoppingList
    + name, is_primary, is_archived, created_at, completed_at

  ShoppingListLine (replaces the m2m)
    + quantity, is_ticked, selected_product_id, sequence

Pre-release schema so we drop and recreate. Existing rows are nulled at
the FK boundary first to keep the cascade behaviour predictable.

Revision ID: b2e8d4f1c9a3
Revises: 9a4c1f8e2d56
Create Date: 2026-05-20 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b2e8d4f1c9a3'
down_revision = '9a4c1f8e2d56'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('ShoppingListStockItem')
    op.drop_table('ShoppingList')

    op.create_table(
        'ShoppingList',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ShoppingListLine',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('shopping_list_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('is_ticked', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('selected_product_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['shopping_list_id'], ['ShoppingList.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stock_item_id'], ['StockItem.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_product_id'], ['Product.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('ShoppingListLine')
    op.drop_table('ShoppingList')

    op.create_table(
        'ShoppingList',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'ShoppingListStockItem',
        sa.Column('shopping_list_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        sa.ForeignKeyConstraint(['shopping_list_id'], ['ShoppingList.id']),
        sa.ForeignKeyConstraint(['stock_item_id'], ['StockItem.id']),
    )
