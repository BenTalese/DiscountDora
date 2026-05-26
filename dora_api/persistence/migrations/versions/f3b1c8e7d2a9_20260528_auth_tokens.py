"""20260528_auth_tokens

Adds the email_verified + password_changed_at columns on User, plus a
new AuthToken table backing email-verify and password-reset flows.

Tokens are stored as a SHA-256 hash so a compromised DB doesn't leak
the raw values from the email links.

Revision ID: f3b1c8e7d2a9
Revises: e9a2c4b1f7d8
Create Date: 2026-05-28 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

# revision identifiers, used by Alembic.
revision = 'f3b1c8e7d2a9'
down_revision = 'e9a2c4b1f7d8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        'AuthToken',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('user_id', UUIDType, sa.ForeignKey('User.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('purpose', sa.String(32), nullable=False),  # "verify_email" | "reset_password" | "change_email"
        sa.Column('payload', sa.String(255), nullable=True),  # new-email candidate for change_email
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_AuthToken_user_purpose', 'AuthToken', ['user_id', 'purpose'])
    op.create_index('ix_AuthToken_expires_at', 'AuthToken', ['expires_at'])


def downgrade():
    op.drop_index('ix_AuthToken_expires_at', table_name='AuthToken')
    op.drop_index('ix_AuthToken_user_purpose', table_name='AuthToken')
    op.drop_table('AuthToken')
    with op.batch_alter_table('User') as batch:
        batch.drop_column('password_changed_at')
        batch.drop_column('email_verified')
