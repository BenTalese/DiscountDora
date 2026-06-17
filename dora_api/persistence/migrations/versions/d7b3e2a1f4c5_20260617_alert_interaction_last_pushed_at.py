"""20260617_alert_interaction_last_pushed_at

C-9.8 — pairs `last_pushed_at` with the existing `last_emailed_at` on
``AlertInteraction``. Per-channel delivery dedup stays on the existing
ledger (PROPOSAL_ALERTS §4.2 + the C-9.7 ADR — one row per (user_id,
alert_key), one timestamp column per channel) rather than splitting out
a sibling delivery table.

Revision ID: d7b3e2a1f4c5
Revises: c4f9a8b3e2d6
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'd7b3e2a1f4c5'
down_revision = 'c4f9a8b3e2d6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AlertInteraction') as batch_op:
        batch_op.add_column(sa.Column(
            'last_pushed_at', sa.DateTime(timezone=True), nullable=True,
        ))


def downgrade():
    with op.batch_alter_table('AlertInteraction') as batch_op:
        batch_op.drop_column('last_pushed_at')
