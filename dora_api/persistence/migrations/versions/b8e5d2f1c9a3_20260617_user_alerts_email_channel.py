"""20260617_user_alerts_email_channel

C-9.7 — adds the alerts-email channel prefs to `User` (PROPOSAL_ALERTS
§3.5 / §4.4): a master enable, a cadence sentinel ('off' | 'daily' |
'weekly'), and a weekly send day (Mon=0 … Sun=6, ignored on the daily
cadence). Defaults are quiet — off + cadence='off' + day=0 — so an
upgraded install delivers nothing until each user opts in. Decoupled
from the deals-email channel on purpose (kept channels independent so
one can be on without the other).

Revision ID: b8e5d2f1c9a3
Revises: e2a9c5f1b7d4
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'b8e5d2f1c9a3'
down_revision = 'e2a9c5f1b7d4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column(
            'alerts_email_enabled', sa.Boolean(),
            nullable=False, server_default='0',
        ))
        batch_op.add_column(sa.Column(
            'alerts_email_cadence', sa.String(length=16),
            nullable=False, server_default='off',
        ))
        batch_op.add_column(sa.Column(
            'alerts_email_day', sa.Integer(),
            nullable=False, server_default='0',
        ))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('alerts_email_day')
        batch_op.drop_column('alerts_email_cadence')
        batch_op.drop_column('alerts_email_enabled')
