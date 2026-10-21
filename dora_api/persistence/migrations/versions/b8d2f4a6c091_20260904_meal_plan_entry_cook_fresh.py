"""20260904_meal_plan_entry_cook_fresh

Owner, 2026-09-04: *"I batch cook, yes. But I also fresh cook. When in batch
mode, I should be able to mark a meal as being cooked fresh and therefore it
should not take a meal, and it should also not demand a meal from the pool. I
batch cook and freeze lunches for the week, but dinner with the parents on
Saturday is fresh."*

Cook-style was install-wide (`AppSetting.batch_features_enabled`) and binary, so
a batch household had no way to say "this one is cooked on the day". This adds
the per-entry exception: `MealPlanEntry.cook_fresh`.

A fresh meal stands outside the cooked-portion pool in both directions — it is
never allocated a portion, and it never adds to what has to be batch-cooked or
decrements the pool on its day. It is still a cook; just not one the pool
answers for.

Additive and non-destructive: every existing row is `False`, which is exactly
what the behaviour was before this column existed.

Revision ID: b8d2f4a6c091
Revises: a7c3e5d19f2b
Create Date: 2026-09-04 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b8d2f4a6c091'
down_revision = 'a7c3e5d19f2b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('MealPlanEntry') as batch:
        batch.add_column(sa.Column(
            'cook_fresh', sa.Boolean(), nullable=False, server_default=sa.false(),
        ))


def downgrade():
    with op.batch_alter_table('MealPlanEntry') as batch:
        batch.drop_column('cook_fresh')
