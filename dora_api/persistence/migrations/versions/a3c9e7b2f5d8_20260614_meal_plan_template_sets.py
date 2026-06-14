"""20260614_meal_plan_template_sets

Meal Plans C-2.G — `MealPlanTemplateSet` + `MealPlanTemplateSetItem` (a rotating
ordered list of templates) and `MealPlan.source_template_set_id` + `rotation_index`
provenance for weeks forked from a set.

Plain create_table (portable SQLite + Postgres) + plain ADD COLUMNs with no DB
FK (provenance only), so they apply natively on SQLite without a table rebuild.
Reversible (R-006).

Revision ID: a3c9e7b2f5d8
Revises: f2b8d4c6a1e3
Create Date: 2026-06-14 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'a3c9e7b2f5d8'
down_revision = 'f2b8d4c6a1e3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'MealPlanTemplateSet',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'MealPlanTemplateSetItem',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('set_id', UUIDType, sa.ForeignKey('MealPlanTemplateSet.id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_id', UUIDType, nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column('MealPlan', sa.Column('source_template_set_id', UUIDType, nullable=True))
    op.add_column('MealPlan', sa.Column('rotation_index', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('MealPlan', 'rotation_index')
    op.drop_column('MealPlan', 'source_template_set_id')
    op.drop_table('MealPlanTemplateSetItem')
    op.drop_table('MealPlanTemplateSet')
