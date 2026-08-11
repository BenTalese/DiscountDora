"""20260811_drop_user_meals_per_week

FU-612 — delete the per-user `meals_per_week` preference end-to-end.

It only ever fed the sequential meal-plan builder's target meal count. The
2026-08-07 builder rework replaced that single number with an explicit
day × meal-slot toggle grid, so nothing reads the value any more — a setting
that does nothing. The column is dropped outright.

**Pre-release hard change — no data preserved:** any stored per-user values are
discarded. SQLite runs it in batch mode (table recreate).

Revision ID: c3f8a1b52d9e
Revises: b9d4f2a7c1e6
Create Date: 2026-08-11 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'c3f8a1b52d9e'
down_revision = 'b9d4f2a7c1e6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('meals_per_week')


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column('meals_per_week', sa.Integer(), nullable=True))
