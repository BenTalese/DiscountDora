"""20260520_shopping_list_templates

Adds the `ShoppingListTemplate` + `ShoppingListTemplateLine` tables behind
the shopping-list "save as template" / "create from template" flows.

Revision ID: c4f7a2b8e1d6
Revises: b2e8d4f1c9a3
Create Date: 2026-05-20 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c4f7a2b8e1d6'
down_revision = 'b2e8d4f1c9a3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ShoppingListTemplate',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ShoppingListTemplateLine',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('template_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['template_id'], ['ShoppingListTemplate.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stock_item_id'], ['StockItem.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('ShoppingListTemplateLine')
    op.drop_table('ShoppingListTemplate')
