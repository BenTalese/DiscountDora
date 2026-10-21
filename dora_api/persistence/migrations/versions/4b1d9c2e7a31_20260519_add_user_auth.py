"""20260519_add_user_auth

Adds the `password_hash` column to the User table for session-based auth.

The mapping in `table_mappings.py` also marks `username` as NOT NULL UNIQUE
so fresh databases pick that up via `db.create_all()`. We intentionally do
NOT enforce those constraints here — on an existing dev DB with seed data
the rewrite is risky (null/dupe usernames pre-migration would break the
batch alter) and the application layer (RegisterUserHandler) already
guarantees username uniqueness on insert.

Revision ID: 4b1d9c2e7a31
Revises: 3a2c8f1d7b4e
Create Date: 2026-05-19 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4b1d9c2e7a31'
down_revision = '3a2c8f1d7b4e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column('password_hash', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('password_hash')
