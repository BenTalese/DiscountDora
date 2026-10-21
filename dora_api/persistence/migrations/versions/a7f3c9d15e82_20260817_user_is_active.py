"""20260817_user_is_active

Owner call 2026-08-17 — admins can deactivate a user instead of deleting them.
Delete is destructive (sessions, alert prefs, push subscriptions go with it);
"this person no longer uses Dora" only needs the door locked.

Default TRUE: every existing account is a working account, and only an explicit
admin action flips it. No data migration.

Revision ID: a7f3c9d15e82
Revises: e5c1a9d7b234
Create Date: 2026-08-17 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import true

revision = 'a7f3c9d15e82'
down_revision = 'e5c1a9d7b234'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column(
            'is_active', sa.Boolean(), nullable=False, server_default=true(),
        ))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('is_active')
