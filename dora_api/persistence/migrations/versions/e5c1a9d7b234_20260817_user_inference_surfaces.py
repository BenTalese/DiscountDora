"""20260817_user_inference_surfaces

FU-653 — the Zero-Input Pantry belief gets surfaced beyond the stock pages
(recipes / shopping lists / meal planner), each behind its own per-user opt-in.

`inferred_pantry_enabled` (a3e8b1f6c2d9) stays exactly as it is and becomes the
*stock* surface's toggle. The three new columns default **FALSE**, not TRUE like
that one: the stock overlay is the headline experience of a page about stock
levels, whereas these annotate pages the user opened to do something else, so
they're opt-in per Charter P10 (anti-creep). No data migration — every existing
user starts with the new surfaces quiet.

Revision ID: e5c1a9d7b234
Revises: d3a7f2b91c60
Create Date: 2026-08-17 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import false

revision = 'e5c1a9d7b234'
down_revision = 'd3a7f2b91c60'
branch_labels = None
depends_on = None


_COLUMNS = (
    'inference_recipes_enabled',
    'inference_shopping_enabled',
    'inference_meal_plan_enabled',
)


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        for name in _COLUMNS:
            batch_op.add_column(sa.Column(
                name, sa.Boolean(), nullable=False, server_default=false(),
            ))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        for name in _COLUMNS:
            batch_op.drop_column(name)
