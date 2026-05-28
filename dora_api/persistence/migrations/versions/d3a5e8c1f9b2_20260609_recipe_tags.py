"""20260609_recipe_tags

P2-08 — recipe-level dietary / allergen-free / nutritional / diet-pattern
tags. The canonical tag vocabulary lives in
`dora_api/domain/recipe_tags.py`; this table just pins which curated
tags belong to which recipe.

Pattern matches StockItemProduct / StockItemSubstitute — a pure
association table with no standalone entity. CASCADE on recipe delete
so the rows go with the recipe.

Revision ID: d3a5e8c1f9b2
Revises: c9f2d6b3e8a1
Create Date: 2026-06-09 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'd3a5e8c1f9b2'
down_revision = 'c9f2d6b3e8a1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'RecipeTag',
        sa.Column(
            'recipe_id', UUIDType,
            sa.ForeignKey('Recipe.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column('tag', sa.String(length=64), primary_key=True),
    )
    # "Find recipes with tag X" is the hot read pattern (filter drawer +
    # Dora's tag-aware suggestion). Index on tag alone covers it; the
    # composite PK already covers the "tags for recipe X" direction.
    op.create_index(
        'ix_recipe_tag_tag',
        'RecipeTag',
        ['tag'],
    )


def downgrade():
    op.drop_index('ix_recipe_tag_tag', table_name='RecipeTag')
    op.drop_table('RecipeTag')
