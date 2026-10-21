"""20260628_drop_recipe_nutrition

FU-115 — drop the freeform `Recipe.nutrition` text column. Replaced
by the structured `kcal: int | None` field added in Cookbook Chunk 9.
Pre-release, no user data preservation required.

Revision ID: b7e2d9a4c1f5
Revises: a1c5e7d4f2b9
Create Date: 2026-06-28 00:00:00.000000

"""
from alembic import op


revision = 'b7e2d9a4c1f5'
down_revision = 'a1c5e7d4f2b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Recipe') as batch:
        batch.drop_column('nutrition')


def downgrade():
    import sqlalchemy as sa
    with op.batch_alter_table('Recipe') as batch:
        batch.add_column(sa.Column('nutrition', sa.String(), nullable=True))
