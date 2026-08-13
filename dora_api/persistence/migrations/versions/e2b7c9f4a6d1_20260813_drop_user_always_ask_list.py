"""20260813_drop_user_always_ask_list

Owner call 2026-08-13 — remove the per-user "always ask which draft list on
quick-add" preference end-to-end. The remembered-pick behaviour it toggled was
retired too: quick-add now always asks which list when more than one draft
exists (multiple lists are deliberate, so silently reusing the last pick was
more annoying than helpful). Nothing reads the column any more, so it's dropped.

**Pre-release hard change — no data preserved:** any stored per-user values are
discarded. SQLite runs it in batch mode (table recreate).

Revision ID: e2b7c9f4a6d1
Revises: d4c8b1f6e903
Create Date: 2026-08-13 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'e2b7c9f4a6d1'
down_revision = 'd4c8b1f6e903'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('always_ask_which_shopping_list')


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column(
            'always_ask_which_shopping_list',
            sa.Boolean(),
            nullable=False,
            server_default='0',
        ))
