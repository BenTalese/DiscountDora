"""20260609_recipe_vocab_tables

C-4 Chunk 2 — turn recipe cuisine / category / dietary-tags into
user-configurable vocabularies.

- New `Cuisine`, `Category`, `DietaryTag` lookup tables ({id, name,
  sequence}; DietaryTag also has a grouping `category` label), seeded with
  sensible defaults.
- `Recipe.cuisine` / `Recipe.category` change from free-text String columns
  to nullable FK columns (`cuisine_id` / `category_id`, ON DELETE SET NULL).
- `RecipeTag` association swaps its `tag` String column for a
  `dietary_tag_id` FK to the new DietaryTag table.

Pre-release: existing recipe cuisine/category strings and RecipeTag rows are
discarded rather than converted (no production data). Re-tag recipes via the
editor after upgrade.

Revision ID: a7d2f4c9e1b8
Revises: e1a4c7b2f9d0
Create Date: 2026-06-09 00:00:00.000000

"""
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'a7d2f4c9e1b8'
down_revision = 'e1a4c7b2f9d0'
branch_labels = None
depends_on = None


_DEFAULT_CUISINES = [
    "Italian", "Asian", "Chinese", "Japanese", "Thai", "Indian",
    "Mexican", "Mediterranean", "American", "French", "Middle Eastern",
    "Other",
]

_DEFAULT_CATEGORIES = [
    "Main", "Pasta", "Rice", "Stir fry", "Soup", "Salad", "Side",
    "Breakfast", "Dessert", "Snack", "Drink", "Sauce",
]

# Mirrors the (now-retired) in-code RECIPE_TAG_CATALOGUE. {name, category}.
_DEFAULT_DIETARY_TAGS = [
    ("Vegetarian", "Dietary pattern"),
    ("Vegan", "Dietary pattern"),
    ("Pescatarian", "Dietary pattern"),
    ("Gluten-free", "Allergen-free"),
    ("Dairy-free", "Allergen-free"),
    ("Nut-free", "Allergen-free"),
    ("Egg-free", "Allergen-free"),
    ("Soy-free", "Allergen-free"),
    ("Shellfish-free", "Allergen-free"),
    ("Low-carb", "Nutritional"),
    ("Low-fat", "Nutritional"),
    ("Low-sugar", "Nutritional"),
    ("Low-sodium", "Nutritional"),
    ("Keto", "Diet pattern"),
    ("Paleo", "Diet pattern"),
    ("Whole30", "Diet pattern"),
    ("Halal", "Religious"),
    ("Kosher", "Religious"),
]


def upgrade():
    op.create_table(
        'Cuisine',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_table(
        'Category',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_table(
        'DietaryTag',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
    )

    _seed_vocabularies()

    # Recipe: drop the free-text columns, add the FK columns. Batch mode so
    # SQLite (which can't ALTER columns in place) rebuilds the table.
    with op.batch_alter_table('Recipe', schema=None) as batch:
        batch.drop_column('cuisine')
        batch.drop_column('category')
        batch.add_column(sa.Column('cuisine_id', UUIDType, nullable=True))
        batch.add_column(sa.Column('category_id', UUIDType, nullable=True))
        batch.create_foreign_key(
            'fk_recipe_cuisine_id', 'Cuisine', ['cuisine_id'], ['id'],
            ondelete='SET NULL',
        )
        batch.create_foreign_key(
            'fk_recipe_category_id', 'Category', ['category_id'], ['id'],
            ondelete='SET NULL',
        )

    # RecipeTag: discard the old string-tag rows and rebuild against the FK.
    op.drop_index('ix_recipe_tag_tag', table_name='RecipeTag')
    op.drop_table('RecipeTag')
    op.create_table(
        'RecipeTag',
        sa.Column(
            'recipe_id', UUIDType,
            sa.ForeignKey('Recipe.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column(
            'dietary_tag_id', UUIDType,
            sa.ForeignKey('DietaryTag.id', ondelete='CASCADE'),
            primary_key=True,
        ),
    )
    op.create_index(
        'ix_recipe_tag_dietary_tag_id',
        'RecipeTag',
        ['dietary_tag_id'],
    )


def _seed_vocabularies():
    cuisine_tbl = sa.table(
        'Cuisine',
        sa.column('id', UUIDType()),
        sa.column('name', sa.String),
        sa.column('sequence', sa.Integer),
    )
    category_tbl = sa.table(
        'Category',
        sa.column('id', UUIDType()),
        sa.column('name', sa.String),
        sa.column('sequence', sa.Integer),
    )
    dietary_tbl = sa.table(
        'DietaryTag',
        sa.column('id', UUIDType()),
        sa.column('name', sa.String),
        sa.column('category', sa.String),
        sa.column('sequence', sa.Integer),
    )

    op.bulk_insert(cuisine_tbl, [
        {'id': str(uuid.uuid4()), 'name': name, 'sequence': i}
        for i, name in enumerate(_DEFAULT_CUISINES)
    ])
    op.bulk_insert(category_tbl, [
        {'id': str(uuid.uuid4()), 'name': name, 'sequence': i}
        for i, name in enumerate(_DEFAULT_CATEGORIES)
    ])
    op.bulk_insert(dietary_tbl, [
        {'id': str(uuid.uuid4()), 'name': name, 'category': category, 'sequence': i}
        for i, (name, category) in enumerate(_DEFAULT_DIETARY_TAGS)
    ])


def downgrade():
    op.drop_index('ix_recipe_tag_dietary_tag_id', table_name='RecipeTag')
    op.drop_table('RecipeTag')
    op.create_table(
        'RecipeTag',
        sa.Column(
            'recipe_id', UUIDType,
            sa.ForeignKey('Recipe.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column('tag', sa.String(length=64), primary_key=True),
    )
    op.create_index('ix_recipe_tag_tag', 'RecipeTag', ['tag'])

    with op.batch_alter_table('Recipe', schema=None) as batch:
        batch.drop_constraint('fk_recipe_cuisine_id', type_='foreignkey')
        batch.drop_constraint('fk_recipe_category_id', type_='foreignkey')
        batch.drop_column('cuisine_id')
        batch.drop_column('category_id')
        batch.add_column(sa.Column('cuisine', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('category', sa.String(length=255), nullable=True))

    op.drop_table('DietaryTag')
    op.drop_table('Category')
    op.drop_table('Cuisine')
