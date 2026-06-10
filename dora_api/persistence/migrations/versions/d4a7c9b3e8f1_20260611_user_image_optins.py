"""20260611_user_image_optins

C-cross Chunk 5 — per-user image-display opt-ins (proposal §2.8).

Two booleans on `User`, both default True — visual richness on by
default (Charter P1 Effortless); users opt out via the inline buttons
on each surface. Image upload/edit/delete keeps working regardless.

Revision ID: d4a7c9b3e8f1
Revises: c8d3f4a9b2e1
Create Date: 2026-06-11 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'd4a7c9b3e8f1'
down_revision = 'c8d3f4a9b2e1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column('show_recipe_images', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('show_stock_images', sa.Boolean(), nullable=False, server_default='1'))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('show_stock_images')
        batch_op.drop_column('show_recipe_images')
