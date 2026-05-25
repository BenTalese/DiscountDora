"""20260524_user_last_backup_at

Adds the User.last_backup_at column. Set every time a user successfully
hits GET /api/data/backup so the Create-backup card can show "last backup
N hours ago". Null for users who haven't taken one yet.

Revision ID: c5e8f3a91b07
Revises: b4d7c1a9e052
Create Date: 2026-05-24 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c5e8f3a91b07'
down_revision = 'b4d7c1a9e052'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'last_backup_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('last_backup_at')
