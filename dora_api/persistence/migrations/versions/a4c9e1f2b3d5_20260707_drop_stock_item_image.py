"""20260707_drop_stock_item_image

FU-508 — drop the half-built per-stock-item image feature. The pantry
photo was never a load-bearing surface: linked Products already carry
the visual, and users who cared about it never got a working upload
UI (only URL-import and paste flows populated `StockItem.image`). Anti-
creep call: remove the column, the upload/serve endpoint, and the
`show_stock_images` render toggle rather than finish it.

Schema changes:
1. Drop ``StockItem.image`` (LargeBinary blob).
2. Drop ``User.show_stock_images`` (Boolean, previously default true).

The companion ``show_recipe_images`` opt-in stays — the recipe-image
render is the surface users actually toggle.

Revision ID: a4c9e1f2b3d5
Revises: e5b4d8f2c3a7
Create Date: 2026-07-07 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'a4c9e1f2b3d5'
down_revision = 'e5b4d8f2c3a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItem') as batch:
        batch.drop_column('image')
    with op.batch_alter_table('User') as batch:
        batch.drop_column('show_stock_images')


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'show_stock_images', sa.Boolean(),
            nullable=False, server_default=sa.true(),
        ))
    with op.batch_alter_table('StockItem') as batch:
        batch.add_column(sa.Column('image', sa.LargeBinary(), nullable=True))
