"""20260614_meal_plan_templates

Meal Plans C-2.F — `MealPlanTemplate` + `MealPlanTemplateEntry` (a saved week
shape, forkable onto any week) and `MealPlan.source_template_id` provenance.

New tables use plain `create_table` (portable SQLite + Postgres). The
`source_template_id` column is a plain ADD COLUMN with **no DB FK** (provenance
only — editing/deleting a template never touches forked plans, Decision 1), so
it applies natively on SQLite without a table rebuild. Reversible (R-006).

Revision ID: f2b8d4c6a1e3
Revises: d2a7f4c9e6b1
Create Date: 2026-06-14 00:00:00.000000

Threads after the concurrent `d2a7f4c9e6b1` (drop_stock_item_preferred_product)
rather than its sibling `e1f7b3d9a2c4`, to keep a single linear head — both
chunks branched from the same parent on the same day. The two migrations are
independent (templates vs. dropping a column), so the order doesn't matter.

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'f2b8d4c6a1e3'
down_revision = 'd2a7f4c9e6b1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'MealPlanTemplate',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'MealPlanTemplateEntry',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('template_id', UUIDType, sa.ForeignKey('MealPlanTemplate.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipe_id', UUIDType, sa.ForeignKey('Recipe.id', ondelete='CASCADE'), nullable=False),
        sa.Column('offset_from_monday', sa.Integer(), nullable=False),
        sa.Column('slot', sa.String(length=50), nullable=False),
        sa.Column('servings', sa.Integer(), nullable=False, server_default='1'),
    )
    op.add_column('MealPlan', sa.Column('source_template_id', UUIDType, nullable=True))


def downgrade():
    op.drop_column('MealPlan', 'source_template_id')
    op.drop_table('MealPlanTemplateEntry')
    op.drop_table('MealPlanTemplate')
