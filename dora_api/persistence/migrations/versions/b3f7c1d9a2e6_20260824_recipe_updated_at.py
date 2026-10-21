"""20260824_recipe_updated_at

Recipe-view feedback 2026-08-24 — the redesigned recipe page's version panel
shows "created" and "last updated" for the recipe. `Recipe.created_at` already
existed (f9d3a7c2b5e8); this adds the edit stamp.

Nullable with no backfill, deliberately: we have no record of when legacy rows
were last edited, and inventing one (created_at, say) would be a lie the panel
then prints as fact. NULL renders as "not edited since it was added".

Revision ID: b3f7c1d9a2e6
Revises: a7d4e91c3f28
Create Date: 2026-08-24 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b3f7c1d9a2e6'
down_revision = 'a7d4e91c3f28'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Recipe') as batch:
        batch.add_column(sa.Column(
            'updated_at', sa.DateTime(timezone=True), nullable=True,
        ))


def downgrade():
    with op.batch_alter_table('Recipe') as batch:
        batch.drop_column('updated_at')
