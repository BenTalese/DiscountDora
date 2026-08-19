"""20260820_alerts_step0_cuts

Step-0 of `docs/04_proposals/IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md` — the
owner's assessment of the alerts system. Three schema consequences, all
deletions:

1. **`AlertPreference.tier_override` (Q3).** Severity is now the single
   importance scale and the actionable/FYI tier is derived from it. A per-user
   tier override made "is this actionable?" a per-user answer the stock rows
   could not see, which is the direct cause of B2 (the bell honoured prefs, the
   row outlines ignored them). Per-kind `enabled` stays — that's the L441 ask.

2. **`User.alerts_email_*` (Q4).** The alerts email digest is cut. Web push
   already delivers the same set instantly and needs no SMTP; the 19:00 daily
   brief covers the digest shape that was actually wanted.

3. **`AlertInteraction.last_emailed_at` (Q4).** The digest's delivery-dedup
   ledger column. `last_pushed_at` is untouched — the push channel survives.

Dropping the columns loses each user's stored tier overrides and email-cadence
choices. Pre-release, per the standing migrations policy, that's acceptable and
no backfill shim is written: there is nowhere to move an override *to* (the
concept is gone), and a cadence for a deleted job is not preference data worth
preserving.

Revision ID: e4b1c7a95d20
Revises: d9f4b2c7e803
Create Date: 2026-08-20 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import false

revision = 'e4b1c7a95d20'
down_revision = 'd9f4b2c7e803'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AlertPreference') as batch_op:
        batch_op.drop_column('tier_override')
    with op.batch_alter_table('AlertInteraction') as batch_op:
        batch_op.drop_column('last_emailed_at')
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('alerts_email_day')
        batch_op.drop_column('alerts_email_cadence')
        batch_op.drop_column('alerts_email_enabled')


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column(
            'alerts_email_enabled', sa.Boolean(), nullable=False,
            server_default=false(),
        ))
        batch_op.add_column(sa.Column(
            'alerts_email_cadence', sa.String(length=16), nullable=False,
            server_default='off',
        ))
        batch_op.add_column(sa.Column(
            'alerts_email_day', sa.Integer(), nullable=False, server_default='0',
        ))
    with op.batch_alter_table('AlertInteraction') as batch_op:
        batch_op.add_column(sa.Column(
            'last_emailed_at', sa.DateTime(timezone=True), nullable=True,
        ))
    with op.batch_alter_table('AlertPreference') as batch_op:
        batch_op.add_column(sa.Column(
            'tier_override', sa.String(length=16), nullable=True,
        ))
