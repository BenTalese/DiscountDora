"""20260611_recipe_kcal

C-4 Chunk 9 — simple nutrition (kcal) column on Recipe.

Single int, nullable. Per-recipe value typed by the user when the
C-cross nutrition opt-in is in `simple` mode. Existing freeform
`nutrition` text column stays for backwards compatibility but is no
longer rendered/edited on the detail page (logged as a follow-up to
drop once we're sure no user has typed something irreplaceable in
there).

Revision ID: e5b9d2c8a4f3
Revises: d4a7c9b3e8f1
Create Date: 2026-06-11 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'e5b9d2c8a4f3'
down_revision = 'd4a7c9b3e8f1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Recipe') as batch_op:
        batch_op.add_column(sa.Column('kcal', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('Recipe') as batch_op:
        batch_op.drop_column('kcal')
