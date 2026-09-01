"""20260901_recipe_step_timer_minutes

Owner feedback on cook mode: *"How does the timer function get added? Is it
guessing? I feel this might be okay for free text but for structured I feel a
tickable box option should be added"*.

It was guessing. Cook mode ran a regex over the step's text looking for
"20 minutes" / "1 hour" and offered a timer when it matched — which is the
only thing a free-text method can support, because there is nowhere on a
line of prose to record "this step is timed". A structured step is a row,
so it can hold the fact outright.

`timer_minutes` is that column. NULL = no declared timer, which keeps the
text sniff as the fallback for every recipe written before this and for the
free-text and photo faces, neither of which has steps to hang a column off.

Additive and nullable — no backfill, no data loss.

Revision ID: a7c3f1e9b482
Revises: e3b1d7f5a904
Create Date: 2026-09-01 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a7c3f1e9b482'
down_revision = 'e3b1d7f5a904'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('RecipeStep') as batch:
        batch.add_column(sa.Column('timer_minutes', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('RecipeStep') as batch:
        batch.drop_column('timer_minutes')
