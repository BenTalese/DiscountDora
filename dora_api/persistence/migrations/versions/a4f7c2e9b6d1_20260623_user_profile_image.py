"""20260623_user_profile_image

Settings rebuild Phase 4 (§2.9) — profile pictures.

Adds one column:

- ``User.image LargeBinary NULL`` — the user's profile picture, stored as a
  data-URL blob (``data:image/...;base64,...`` encoded to bytes), exactly
  like ``Store.image`` / ``StockItem.image``. NULL = no picture (the common
  case; the menu bar falls back to the person icon, the avatars to initials).
  Deferred at the ORM mapper so list endpoints never drag the bytes per row;
  ``has_image`` is derived from a separate IS-NOT-NULL select.

Postgres + SQLite both support ``ADD COLUMN ... NULL`` without a table
rewrite, so this is a cheap migration (R-005 / R-006). Batch mode keeps
SQLite happy and constraint names deterministic (R-015).

Revision ID: a4f7c2e9b6d1
Revises: d7b3e8f2a5c4
Create Date: 2026-06-23 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'a4f7c2e9b6d1'
down_revision = 'd7b3e8f2a5c4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(
            sa.Column('image', sa.LargeBinary(), nullable=True),
        )


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('image')
