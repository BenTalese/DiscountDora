"""20260630_shopping_list_attachment

FU-334 — receipt-photo record-keeping. New ``ShoppingListAttachment``
child table holding one ordered photo per attached receipt on a
shopping list. Storage shape mirrors ``RecipeStepImage``: image blob is
the encoded ``data:image/...;base64,...`` UTF-8 bytes; the bytes
endpoint at ``GET /shopping-lists/<list_id>/attachments/<attachment_id>``
decodes + serves raw.

Pre-release: no idempotent guards.

Revision ID: a4c8f2e1b9d3
Revises: e5b9d3c7a8f2
Create Date: 2026-06-30 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType


revision = 'a4c8f2e1b9d3'
down_revision = 'e5b9d3c7a8f2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ShoppingListAttachment',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column(
            'shopping_list_id', UUIDType,
            sa.ForeignKey('ShoppingList.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('image', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        'ix_shopping_list_attachment_shopping_list_id',
        'ShoppingListAttachment', ['shopping_list_id'],
    )


def downgrade():
    op.drop_index(
        'ix_shopping_list_attachment_shopping_list_id',
        table_name='ShoppingListAttachment',
    )
    op.drop_table('ShoppingListAttachment')
