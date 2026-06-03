"""20260612_meal_to_recipe_pool

Collapse the Meal entity into Recipe. Recipes gain an `available_meals`
pool count; MealPlanEntry now points directly at a Recipe and stamps
`consumed_at` when a day rolls past.

Pre-release: old Meal data is discarded rather than migrated.

Revision ID: b2c3d4e5f6a7
Revises: f2a8c5d9e3b7
Create Date: 2026-06-12 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'b2c3d4e5f6a7'
down_revision = 'f2a8c5d9e3b7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'Recipe',
        sa.Column('available_meals', sa.Integer(), nullable=False, server_default='0'),
    )

    # Drop the old MealPlanEntry → Meal link and the Meal tables. Existing
    # entries are discarded (pre-release, no production data).
    op.drop_table('MealPlanEntry')
    op.drop_table('MealRecipe')
    op.drop_table('Meal')

    op.create_table(
        'MealPlanEntry',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('recipe_id', UUIDType, sa.ForeignKey('Recipe.id', ondelete='CASCADE'), nullable=False),
        sa.Column('meal_plan_id', UUIDType, sa.ForeignKey('MealPlan.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scheduled_for', sa.Date(), nullable=False),
        sa.Column('servings', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('slot', sa.String(50), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        'ix_mealplanentry_reconcile',
        'MealPlanEntry',
        ['scheduled_for', 'consumed_at'],
    )


def downgrade():
    op.drop_index('ix_mealplanentry_reconcile', table_name='MealPlanEntry')
    op.drop_table('MealPlanEntry')

    op.create_table(
        'Meal',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('quantity_in_stock', sa.Integer(), nullable=False),
    )
    op.create_table(
        'MealRecipe',
        sa.Column('meal_id', UUIDType, sa.ForeignKey('Meal.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('recipe_id', UUIDType, sa.ForeignKey('Recipe.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table(
        'MealPlanEntry',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('meal_id', UUIDType, sa.ForeignKey('Meal.id', ondelete='CASCADE'), nullable=False),
        sa.Column('meal_plan_id', UUIDType, sa.ForeignKey('MealPlan.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scheduled_for', sa.Date(), nullable=False),
        sa.Column('servings', sa.Integer(), nullable=False),
        sa.Column('slot', sa.String(50), nullable=False),
    )
    op.drop_column('Recipe', 'available_meals')
