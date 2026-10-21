"""20260518_add_recipes_meals

Adds the Recipe / RecipeCollection / RecipeIngredient tables and the
Meal / MealPlan / MealPlanEntry tables (with their many-to-many bridge).

Note on FK cascades: the new tables created here have `ondelete` clauses
baked into their `ForeignKeyConstraint` definitions. The *existing* tables'
FKs (StockItem → StockLevel etc.) gained `ondelete` clauses in
`dora_api/persistence/table_mappings.py` but rewriting those constraints
in-place via Alembic requires the precise auto-generated constraint names,
which differ between SQLite (no names) and Postgres/MySQL. Re-applying them
here would block `flask db upgrade` on the SQLite dev DB.

If you need those cascades enforced on an existing prod DB, run
    flask db migrate -m "apply_fk_cascades"
to autogenerate a follow-up migration with the engine-specific names, then
review it before applying.

Revision ID: 3a2c8f1d7b4e
Revises: d9eba05a2f1b
Create Date: 2026-05-18 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = '3a2c8f1d7b4e'
down_revision = 'd9eba05a2f1b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'RecipeCollection',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'Recipe',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('cook_time_minutes', sa.Integer(), nullable=True),
        sa.Column('cuisine', sa.String(length=255), nullable=True),
        sa.Column('difficulty', sa.String(length=50), nullable=True),
        sa.Column('image', sa.LargeBinary(), nullable=True),
        sa.Column('instructions', sa.String(), nullable=True),
        sa.Column('is_favourite', sa.Boolean(), nullable=False),
        sa.Column('last_made_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('nutrition', sa.String(), nullable=True),
        sa.Column('prep_time_minutes', sa.Integer(), nullable=True),
        sa.Column('recipe_collection_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        sa.Column('servings', sa.Integer(), nullable=True),
        sa.Column('time_of_day', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(
            ['recipe_collection_id'], ['RecipeCollection.id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'RecipeIngredient',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('recipe_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['Recipe.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stock_item_id'], ['StockItem.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'Meal',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('quantity_in_stock', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'MealRecipe',
        sa.Column('meal_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('recipe_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.ForeignKeyConstraint(['meal_id'], ['Meal.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipe_id'], ['Recipe.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('meal_id', 'recipe_id'),
    )

    op.create_table(
        'MealPlan',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'MealPlanEntry',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('meal_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('meal_plan_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('scheduled_for', sa.Date(), nullable=False),
        sa.Column('servings', sa.Integer(), nullable=False),
        sa.Column('slot', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['meal_id'], ['Meal.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['meal_plan_id'], ['MealPlan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('MealPlanEntry')
    op.drop_table('MealPlan')
    op.drop_table('MealRecipe')
    op.drop_table('Meal')
    op.drop_table('RecipeIngredient')
    op.drop_table('Recipe')
    op.drop_table('RecipeCollection')
