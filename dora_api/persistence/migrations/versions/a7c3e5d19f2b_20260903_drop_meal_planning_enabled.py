"""20260903_drop_meal_planning_enabled

Owner, on Settings → Admin → Features: *"what does the meal planning toggle
actually do? I feel like this was added accidentally. Why turn this feature
off? It feels pretty core to the app function."*

Right on both counts. The toggle's own caption claimed it "hides the meal-plans
surface when off" — it never did. The `Meal Plans` main-nav entry and the
`/meal-plans` route are unconditional, and no page, guard or component read the
flag. What it actually governed was one unrelated thing: the planned-demand
signal short-circuited to `enabled: false` when it was off, which is why the
flag looked load-bearing from the API side while doing nothing a user could see.

Meal planning is core to the app, so there is nothing here to turn off. The
column goes, the `features.meal_planning` health flag goes, and planned demand
becomes unconditional — an empty `demand` map already says everything the
`enabled: false` used to.

Destructive by design: an install-wide feature switch, not data. Nothing derives
from it and nothing references it. The downgrade restores it with its original
`server_default='1'`, which is the value every row carried anyway (it shipped
True and the only way to change it was the toggle now removed).

Revision ID: a7c3e5d19f2b
Revises: a7c3f1e9b482
Create Date: 2026-09-03 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a7c3e5d19f2b'
down_revision = 'a7c3f1e9b482'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('meal_planning_enabled')


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'meal_planning_enabled', sa.Boolean(), nullable=False,
            server_default='1',
        ))
