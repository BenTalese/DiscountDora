"""20260612_drop_shopping_list_is_primary

P6-01 Chunk 2. Drops `ShoppingList.is_primary` — "primary" is now inferred
from DRAFT-count at read time (see primary_target_resolver.py), so the stored
flag is dead weight.

Pre-release, so no dual-read shim: the backend no longer reads or writes the
column, and Chunk 2 removes it in the same PR.

Batch mode so the column drop works on SQLite (table rebuild) as well as
Postgres — R-005 portable data access.

Revision ID: d5e9f3b2a1c8
Revises: c4d8e1a6f3b9
Create Date: 2026-06-13 09:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'd5e9f3b2a1c8'
down_revision = 'c4d8e1a6f3b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingList') as batch:
        batch.drop_column('is_primary')


def downgrade():
    with op.batch_alter_table('ShoppingList') as batch:
        batch.add_column(sa.Column(
            'is_primary', sa.Boolean(), nullable=False, server_default='0',
        ))
