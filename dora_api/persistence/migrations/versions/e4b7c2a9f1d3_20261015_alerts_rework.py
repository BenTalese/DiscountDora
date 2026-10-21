"""20261015_alerts_rework

Three schema changes from the 2026-10-15 owner batch:

* `User.alert_discard_after_days` (int, nullable, default 14): alerts whose
  condition began longer ago than this drop out of the user's bell.
* `AlertInteraction.read_at` dropped: there is no read state any more, dismiss
  is the one way to put an alert away.
* `AppSetting.deals_email_enabled` dropped: the weekly deals email now sends
  whenever email is set up and the person has opted in.

Alert keys also gained an episode suffix (an expiry date, a level-change day, a
planned shop date), so interactions recorded against the old keys simply stop
matching anything. Pre-release, they are left in place rather than migrated.

Revision ID: e4b7c2a9f1d3
Revises: c3e8a5f1d7b4
Create Date: 2026-10-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'e4b7c2a9f1d3'
down_revision = 'c3e8a5f1d7b4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'alert_discard_after_days', sa.Integer(), nullable=True, server_default='14',
        ))
    with op.batch_alter_table('AlertInteraction') as batch:
        batch.drop_column('read_at')
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('deals_email_enabled')


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'deals_email_enabled', sa.Boolean(), nullable=False, server_default=sa.false(),
        ))
    with op.batch_alter_table('AlertInteraction') as batch:
        batch.add_column(sa.Column('read_at', sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table('User') as batch:
        batch.drop_column('alert_discard_after_days')
