"""20260606_user_budget

P2-05 — adds an optional grocery budget to the User table:
  - budget_amount  (Float, nullable; NULL = feature off)
  - budget_period  (String, NOT NULL, default 'weekly')

Cross-shopping-list: spend is summed across every archived shopping list
whose `completed_at` falls inside the rolling period, so the budget tracks
the household's whole groceries spend, not a single list.

Revision ID: a6e3b5d2c8f1
Revises: f5c2a7e91b08
Create Date: 2026-06-06 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'a6e3b5d2c8f1'
down_revision = 'f5c2a7e91b08'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column('budget_amount', sa.Float(), nullable=True))
        batch.add_column(sa.Column(
            'budget_period', sa.String(length=16),
            nullable=False, server_default='weekly',
        ))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('budget_period')
        batch.drop_column('budget_amount')
