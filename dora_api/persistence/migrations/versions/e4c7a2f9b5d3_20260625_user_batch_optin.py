"""20260625_user_batch_optin

IMPL_PLAN_MEAL_PLANS_REBUILD §6.6 / Q3 — per-user batch-cooking posture.

Adds `User.batch_features_enabled bool` (default False — fresh-cooker
households see a pure scheduling planner). When the user opts in, the
meal-planner surfaces the cook-pool affordances (recipe pool ± /
log-cook / "n free"), the shortfall warning, and the "to cook by"
sidebar line.

Mirrors `b5c1d9a4e3f2_20260611_user_money_optin` (the same shape +
default + Charter P10 Anti-creep rationale). Pre-release: no idempotent
guards.

Revision ID: e4c7a2f9b5d3
Revises: d3a8f1c5e2b9
Create Date: 2026-06-25 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'e4c7a2f9b5d3'
down_revision = 'd3a8f1c5e2b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column('batch_features_enabled', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('batch_features_enabled')
