"""20260617_alert_interaction_last_emailed_at

C-9.7 — adds `last_emailed_at` to `AlertInteraction` (PROPOSAL_ALERTS
§4.2 decision: single column on the existing ledger, not a sibling
`AlertDelivery` table — dedup stays coarse). Set by the digest job when
an alert is emailed; cleared by the same job on the next run if the
alert key drops out of the user's actionable set, so a later re-fire of
the same condition sends fresh.

Revision ID: c4f9a8b3e2d6
Revises: b8e5d2f1c9a3
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'c4f9a8b3e2d6'
down_revision = 'b8e5d2f1c9a3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AlertInteraction') as batch_op:
        batch_op.add_column(sa.Column(
            'last_emailed_at', sa.DateTime(timezone=True), nullable=True,
        ))


def downgrade():
    with op.batch_alter_table('AlertInteraction') as batch_op:
        batch_op.drop_column('last_emailed_at')
