"""20260626_recipe_created_at

FU-082 — add `Recipe.created_at` so the cookbook overview can land its
"Recently added" sort axis (IMPL_PLAN_COOKBOOK Chunk 1 listed five
axes; this is the missing fifth).

Backfill strategy for existing rows: use `last_made_on` when present
(it's the only existing time signal on the row), otherwise fall back to
the current timestamp. That keeps the relative order intact for any
recipe the user has cooked, and gives unmade legacy recipes a stable
"added today" anchor — newer ones will simply sort above them as the
user creates them, which matches the axis's "Recently added" intent.

Revision ID: f9d3a7c2b5e8
Revises: e4c7a2f9b5d3
Create Date: 2026-06-26 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f9d3a7c2b5e8'
down_revision = 'e4c7a2f9b5d3'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Add the column nullable so we can backfill before the NOT NULL flip.
    with op.batch_alter_table('Recipe') as batch:
        batch.add_column(sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=True,
        ))

    # 2) Backfill: prefer last_made_on, else now(). One UPDATE, portable.
    op.execute(
        'UPDATE "Recipe" '
        'SET created_at = COALESCE(last_made_on, CURRENT_TIMESTAMP) '
        'WHERE created_at IS NULL'
    )

    # 3) Tighten to NOT NULL now that every row has a value.
    with op.batch_alter_table('Recipe') as batch:
        batch.alter_column('created_at', nullable=False)


def downgrade():
    with op.batch_alter_table('Recipe') as batch:
        batch.drop_column('created_at')
