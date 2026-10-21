"""20260614_meal_plan_name_nullable

Meal Plans C-2.E — meal-plan *instances* no longer carry a user name (the UI
shows "Week starting <date>"); the column becomes nullable so the planner can
create nameless week-plans. Templates keep their name (separate entity, C-2.F).

Batch mode: SQLite can't ALTER a column in place, so the table is recreated.
`MealPlan` has no constraints to reproduce (id PK + scalars only), so this is
clear of the FU-178 batch constraint-naming issue. Postgres issues a plain
DROP NOT NULL. Reversible (R-006) — downgrade re-imposes NOT NULL, which
requires no NULL names to be present.

Revision ID: e1f7b3d9a2c4
Revises: c3a7e1f9d4b6
Create Date: 2026-06-14 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'e1f7b3d9a2c4'
down_revision = 'c3a7e1f9d4b6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('MealPlan') as batch_op:
        batch_op.alter_column('name', existing_type=sa.String(length=255), nullable=True)


def downgrade():
    with op.batch_alter_table('MealPlan') as batch_op:
        batch_op.alter_column('name', existing_type=sa.String(length=255), nullable=False)
