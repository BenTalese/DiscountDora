"""20260709_meal_reconcile_receipts

FU-317 Chunk 1 — install-wide `AppSetting.auto_drain_past_meals` toggle
(default TRUE) + append-only `MealPlanReconcileReceipt` audit table. Both
land forward-only, additive; no backfill.

Chunk 1 shape (see IMPL_PLAN_MEAL_RECONCILE.md):
  - `AppSetting.auto_drain_past_meals` — the household-shared posture
    (D5 resolved 2026-07-09 install-wide; FU-517). TRUE keeps today's
    silent auto-drain; FALSE flips the sweep to write receipts but
    leave `MealPlanEntry.consumed_at` and `Recipe.available_meals`
    untouched — the reconcile page is then the mutation surface.
  - `MealPlanReconcileReceipt` — one row per reconcile event per entry,
    never mutated in place. Corrective decisions write a new receipt
    row against the same entry. Matches the `MealPlanSwapLedger`
    (FU-451) shape.

Revision ID: a1b7f3e9c2d4
Revises: f4b2d8e6a1c3
Create Date: 2026-07-09 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType


revision = 'a1b7f3e9c2d4'
down_revision = 'f4b2d8e6a1c3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(
            sa.Column(
                'auto_drain_past_meals',
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )

    op.create_table(
        'MealPlanReconcileReceipt',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('meal_plan_entry_id', UUIDType(), nullable=False),
        sa.Column('state', sa.String(length=32), nullable=False),
        sa.Column('original_servings', sa.Integer(), nullable=False),
        sa.Column('actual_servings', sa.Integer(), nullable=True),
        sa.Column('cooked_on', sa.Date(), nullable=True),
        sa.Column('resolved_by_user_id', UUIDType(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['meal_plan_entry_id'], ['MealPlanEntry.id'], ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['resolved_by_user_id'], ['User.id'], ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_meal_reconcile_receipt_state_created_at',
        'MealPlanReconcileReceipt',
        ['state', 'created_at'],
    )


def downgrade():
    op.drop_index(
        'ix_meal_reconcile_receipt_state_created_at',
        table_name='MealPlanReconcileReceipt',
    )
    op.drop_table('MealPlanReconcileReceipt')
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('auto_drain_past_meals')
