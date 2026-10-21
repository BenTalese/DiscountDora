"""20260811_cook_batches

PROPOSAL_MEAL_PLANS_PART_2 — the cook-batch primitive: one planned cook feeding
several linked meal-plan entries (same recipe + slot, distinct days).

Adds:
  * `CookBatch` table — plan-scoped (CASCADE with the MealPlan), recipe FK anchor.
  * `MealPlanEntry.cook_batch_id` — nullable FK->CookBatch, SET NULL (deleting a
    batch un-links its meals rather than deleting them).
  * FK covering indexes for all three new FK columns (R-034).

Additive + portable (SQLite batch mode for the new column; plain CREATE TABLE /
CREATE INDEX otherwise) — R-005/R-006. Pre-release: nothing to back-fill.

Revision ID: d5a9f27c4e18
Revises: c3f8a1b52d9e
Create Date: 2026-08-11 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType


revision = 'd5a9f27c4e18'
down_revision = 'c3f8a1b52d9e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'CookBatch',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('meal_plan_id', UUIDType(), nullable=False),
        sa.Column('recipe_id', UUIDType(), nullable=False),
        sa.ForeignKeyConstraint(['meal_plan_id'], ['MealPlan.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipe_id'], ['Recipe.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cook_batch_meal_plan_id', 'CookBatch', ['meal_plan_id'])
    op.create_index('ix_cook_batch_recipe_id', 'CookBatch', ['recipe_id'])

    with op.batch_alter_table('MealPlanEntry') as batch_op:
        batch_op.add_column(sa.Column('cook_batch_id', UUIDType(), nullable=True))
        batch_op.create_foreign_key(
            'fk_meal_plan_entry_cook_batch_id', 'CookBatch',
            ['cook_batch_id'], ['id'], ondelete='SET NULL',
        )
        batch_op.create_index('ix_meal_plan_entry_cook_batch_id', ['cook_batch_id'])


def downgrade():
    with op.batch_alter_table('MealPlanEntry') as batch_op:
        batch_op.drop_index('ix_meal_plan_entry_cook_batch_id')
        batch_op.drop_constraint('fk_meal_plan_entry_cook_batch_id', type_='foreignkey')
        batch_op.drop_column('cook_batch_id')
    op.drop_index('ix_cook_batch_recipe_id', table_name='CookBatch')
    op.drop_index('ix_cook_batch_meal_plan_id', table_name='CookBatch')
    op.drop_table('CookBatch')
