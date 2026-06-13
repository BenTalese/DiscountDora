"""20260614_drop_finish_snapshot

FU-163 — undo/reopen retired. The server-owned `finish_snapshot` JSON column
on ShoppingList only existed to let Reopen reverse a finish from the prior
stock levels. With Reopen gone (once a list is done, it's done), the column
is dead weight, so drop it.

Batch mode so the column drop works on SQLite (table rebuild) as well as
Postgres — R-005 portable data access.

Revision ID: a1c4e7b3f5d2
Revises: f3a9c1e5d2b7
Create Date: 2026-06-14 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'a1c4e7b3f5d2'
down_revision = 'f3a9c1e5d2b7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingList') as batch:
        batch.drop_column('finish_snapshot')


def downgrade():
    with op.batch_alter_table('ShoppingList') as batch:
        batch.add_column(sa.Column('finish_snapshot', sa.String(), nullable=True))
