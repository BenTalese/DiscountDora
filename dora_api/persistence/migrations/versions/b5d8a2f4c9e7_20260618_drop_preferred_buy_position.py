"""20260618_drop_preferred_buy_position

FU-225 — drop `PreferredBuy.position`. The round-3 stock-item-detail
feedback pass retired the manual reorder UI; the SPA now sorts preferred
buys alphabetically client-side. The column had no remaining consumer
after the SPA change, and the `PATCH /stock-items/<id>/preferred-buys/reorder`
endpoint was removed in the same commit as this migration.

Revision ID: b5d8a2f4c9e7
Revises: a3e9f6c2d8b4
Create Date: 2026-06-18 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'b5d8a2f4c9e7'
down_revision = 'a3e9f6c2d8b4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('PreferredBuy') as batch_op:
        batch_op.drop_column('position')


def downgrade():
    # Restored as nullable=False with the original server_default so existing
    # rows survive a downgrade; new rows would land with position=0 (the SPA
    # ignores the column post-FU-225 either way).
    with op.batch_alter_table('PreferredBuy') as batch_op:
        batch_op.add_column(
            sa.Column(
                'position', sa.Integer(), nullable=False, server_default='0',
            ),
        )
