"""20260610_recipe_source

C-4 Chunk 7 — `Recipe.source` column.

The URL importer used to append `Source: <url>` to `instructions`; that
made it impossible to render the source as a real link and made the
instructions blob noisier than it should be. Recipes get a dedicated
nullable column. No data migration — existing recipes' `instructions`
text may still mention a URL; parsing it back out reliably is
impractical, so users clean up on edit.

Revision ID: d0e5f1a3b8c7
Revises: c9d4f8e2a5b6
Create Date: 2026-06-10 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'd0e5f1a3b8c7'
down_revision = 'c9d4f8e2a5b6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Recipe') as batch_op:
        batch_op.add_column(sa.Column('source', sa.String(length=2048), nullable=True))


def downgrade():
    with op.batch_alter_table('Recipe') as batch_op:
        batch_op.drop_column('source')
