"""20260703_consumption_event

P6-07 (FU-449) — the missing depletion leg of the closed loop. An
append-only log of a stock item being drawn DOWN (by cooking, a manual
level drop, or waste), so run-out prediction (P6-04) and the Zero-Input
Pantry belief (P8-07) can blend consumption rhythm with purchase rhythm.

Distinct from CookEvent (recipe-scoped). This is stock-item-scoped: one
cook can spawn several consumption events (one per depleted ingredient).
FKs are SET NULL so history survives item/recipe delete; denormalised
names keep rows legible. Pre-release: no idempotent guards.

Same shape as the CookEvent table (c3d7f1a2b8e4).

Revision ID: f2a9c4d7e1b8
Revises: d7e3b9f4a1c2
Create Date: 2026-07-03 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'f2a9c4d7e1b8'
down_revision = 'd7e3b9f4a1c2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ConsumptionEvent',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column(
            'stock_item_id', UUIDType,
            sa.ForeignKey('StockItem.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('stock_item_name', sa.String(length=255), nullable=False),
        sa.Column(
            'recipe_id', UUIDType,
            sa.ForeignKey('Recipe.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('recipe_name', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=16), nullable=False),
        sa.Column('from_sequence', sa.Integer(), nullable=True),
        sa.Column('to_sequence', sa.Integer(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    )
    # Belief + cadence scan by stock_item_id and sort by occurred_at.
    op.create_index(
        'consumption_event_stock_item_id',
        'ConsumptionEvent', ['stock_item_id'],
    )


def downgrade():
    op.drop_index('consumption_event_stock_item_id', table_name='ConsumptionEvent')
    op.drop_table('ConsumptionEvent')
