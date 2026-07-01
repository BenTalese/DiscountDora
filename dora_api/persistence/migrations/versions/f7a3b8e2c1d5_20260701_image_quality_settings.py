"""20260701_image_quality_settings

FU-345 — install-wide image compression knobs. Applies to every upload
surface (stock items, recipes, products, profile pictures, receipts,
store logos) at write time via the shared `processImageFile` helper.
Existing images are left alone; this is a forward-only setting.

- `image_quality` (int, default 85, range 30–100). JPEG/WebP quality
  parameter passed through by the client-side helper. 85 leaves images
  visually indistinguishable from "original"; 60–70 lets disk-conscious
  admins reclaim space.
- `image_max_dimension` (int, default 1920). Cap on the longest edge in
  pixels — anything above is scaled down before encode. Complements the
  existing hard byte cap on the request schema.

Revision ID: f7a3b8e2c1d5
Revises: e5f9c2a8b4d6
Create Date: 2026-07-01 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = 'f7a3b8e2c1d5'
down_revision = 'e5f9c2a8b4d6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'image_quality', sa.Integer(),
            nullable=False, server_default='85',
        ))
        batch.add_column(sa.Column(
            'image_max_dimension', sa.Integer(),
            nullable=False, server_default='1920',
        ))


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('image_max_dimension')
        batch.drop_column('image_quality')
