"""20260616_user_household_headcount

Onboarding C-5.4 — `User.household_headcount` (PROPOSAL_ONBOARDING §3.4).

A single nullable integer: how many people the household usually cooks for.
NULL = not set, in which case cook mode falls back to each recipe's own
`servings`. Set in onboarding; read by RecipeCookMode to seed its per-session
serving scaler (resolves the RecipeCookMode TODO).

Revision ID: e2a9c5f1b7d4
Revises: d1f4b8c3e7a9
Create Date: 2026-06-16 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'e2a9c5f1b7d4'
down_revision = 'd1f4b8c3e7a9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column('household_headcount', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('household_headcount')
