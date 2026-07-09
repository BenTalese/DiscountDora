"""20260709_user_good_deal_threshold

FU-450 — per-user threshold for the proactive ``good_deal`` alert. Adds
``User.good_deal_alert_threshold`` (String(16), NOT NULL, server_default
``'good'``). ``'good'`` nudges on both the ``good`` and ``great`` deal
bands; ``'great'`` restricts to the top band only. No ``fair``/``poor``
option — the whole point is nudges for *real* deals, not noise
(PROPOSAL_BUDGET_DEFENSE_SWAPS §4b).

Default ``'good'`` keeps the alert useful out of the box for money-features
users; it never fires while money features are off (install-wide
``money_enabled`` AND per-user ``money_features_enabled``).

Revision ID: d2f8a1c4b7e9
Revises: c7d1a9e3f2b6
Create Date: 2026-07-09 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'd2f8a1c4b7e9'
down_revision = 'c7d1a9e3f2b6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'good_deal_alert_threshold', sa.String(length=16),
            nullable=False, server_default='good',
        ))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('good_deal_alert_threshold')
