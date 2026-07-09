"""20260709_meal_plan_swap_ledger

FU-451 — append-only ledger of applied budget-defense recipe swaps, so undo is
deterministic and audit-visible (PROPOSAL_BUDGET_DEFENSE_SWAPS §7c). One row per
apply; `undone`/`undone_at` flip when reversed. `payload_json` freezes the
pre-apply state (recipe swap: entry_id + from_recipe_id + from_servings).

Revision ID: e3a9c7b1f2d8
Revises: d2f8a1c4b7e9
Create Date: 2026-07-09 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType


revision = 'e3a9c7b1f2d8'
down_revision = 'd2f8a1c4b7e9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'MealPlanSwapLedger',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('meal_plan_id', UUIDType(), nullable=False),
        sa.Column('applied_by_user_id', UUIDType(), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('kind', sa.String(length=16), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('undone', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('undone_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['meal_plan_id'], ['MealPlan.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['applied_by_user_id'], ['User.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('MealPlanSwapLedger')
