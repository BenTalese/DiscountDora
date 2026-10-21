"""20260817_user_daily_brief

Owner call 2026-08-17 — one opt-in evening push summarising tomorrow's meals
and any shopping day that's due, instead of per-slot cooking reminders.

Per-slot was costed and rejected: five slots across seven days is up to 35
notifications a week, which trains the user to ignore the channel (Charter P10
Anti-creep). The daily brief is 7 at most, and is silent on days with nothing
to say — so in practice fewer.

Default FALSE: every notification channel on this install is opt-in
(matches `alerts_email_enabled` / `deals_email_enabled`). No data migration.

Revision ID: f2a9c4e18b73
Revises: b6e04c9a2f18
Create Date: 2026-08-17 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import false

revision = 'f2a9c4e18b73'
down_revision = 'b6e04c9a2f18'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column(
            'daily_brief_enabled', sa.Boolean(), nullable=False,
            server_default=false(),
        ))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('daily_brief_enabled')
