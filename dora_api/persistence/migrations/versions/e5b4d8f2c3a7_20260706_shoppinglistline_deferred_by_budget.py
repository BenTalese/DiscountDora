"""20260706_shoppinglistline_deferred_by_budget

FU-448 — trim-to-budget optimiser (PROPOSAL_BUDGET_AWARE_LISTS §7.2).
Two columns on ShoppingListLine so the "Trim to fit" pass can set lines
aside without deleting them, with a frozen reason chip. The chip vocab
is closed (brief §5) so a 64-char string is more than enough; NULL
means the line was deferred manually (future path) or via a legacy
trim pass that predates chip storage.

Revision ID: e5b4d8f2c3a7
Revises: a3e7d2c9b5f1
Create Date: 2026-07-06 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'e5b4d8f2c3a7'
down_revision = 'a3e7d2c9b5f1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingListLine') as batch:
        batch.add_column(sa.Column(
            'deferred_by_budget', sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ))
        batch.add_column(sa.Column(
            'deferred_reason', sa.String(64), nullable=True,
        ))


def downgrade():
    with op.batch_alter_table('ShoppingListLine') as batch:
        batch.drop_column('deferred_reason')
        batch.drop_column('deferred_by_budget')
