"""20260703_user_meals_per_week

FU-181 (loose-end 2) — per-user `meals_per_week` preference. Drives the
sequential builder's target-count (`BUILDER_TARGET_MEALS`), currently
hardcoded to 7. NULL = "not set" → the builder falls back to 7.
Range enforced at the request-model boundary (1–21).

Same shape as the earlier `always_ask_which_shopping_list` opt-in
(`c6d2a8e3b9f1_20260703_user_always_ask_list`) and the
`household_headcount` nullable-int pref. Pre-release: no idempotent
guards.

Revision ID: d7e3b9f4a1c2
Revises: c6d2a8e3b9f1
Create Date: 2026-07-03 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'd7e3b9f4a1c2'
down_revision = 'c6d2a8e3b9f1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column('meals_per_week', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('meals_per_week')
