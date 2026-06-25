"""20260624_drop_waste_event_extras

C-waste — slim StockItemWasteEvent to reason-only capture per
`PROPOSAL_WASTE_MINIMISATION.md` §6.1. Drop quantity / estimated_value /
note. Pre-release, clean DROP COLUMN; no idempotent guards.

Revision ID: c2d4a9f7b1e8
Revises: b9e1d4f7a2c8
Create Date: 2026-06-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c2d4a9f7b1e8'
down_revision = 'b9e1d4f7a2c8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItemWasteEvent') as batch_op:
        batch_op.drop_column('quantity')
        batch_op.drop_column('estimated_value')
        batch_op.drop_column('note')


def downgrade():
    with op.batch_alter_table('StockItemWasteEvent') as batch_op:
        batch_op.add_column(sa.Column('quantity', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('estimated_value', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('note', sa.String(), nullable=True))
