"""20260522_user_onboarding_completed

Adds the User.onboarding_completed_at column used by F1's first-run
wizard. Null until the user finishes or skips; cleared by Settings →
Account "Restart onboarding". Existing users (developers, seed data)
land at NULL after upgrade so the wizard surfaces — manually setting
NOW() backfills them out if needed.

Revision ID: b4d7c1a9e052
Revises: a1b2c3d4e5f6
Create Date: 2026-05-22 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b4d7c1a9e052'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'onboarding_completed_at',
            sa.DateTime(),
            nullable=True,
        ))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('onboarding_completed_at')
