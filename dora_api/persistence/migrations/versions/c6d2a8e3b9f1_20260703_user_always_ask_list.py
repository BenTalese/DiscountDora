"""20260703_user_always_ask_list

FU-316 — per-user "Always ask which list when I have more than one draft"
setting for quick-add. Adds `User.always_ask_which_shopping_list bool`,
default False (current behaviour preserved: `useQuickAddTargetPick`
remembers the picked list for the tab session). When True, the SPA skips
the remembered pick so the picker fires every quick-add.

Mirrors the shape of the `batch_features_enabled` opt-in migration
(`e4c7a2f9b5d3_20260625_user_batch_optin`). Pre-release: no idempotent
guards.

Revision ID: c6d2a8e3b9f1
Revises: a1c7d9e42be0
Create Date: 2026-07-03 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'c6d2a8e3b9f1'
down_revision = 'a1c7d9e42be0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column(
            'always_ask_which_shopping_list',
            sa.Boolean(),
            nullable=False,
            server_default='0',
        ))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('always_ask_which_shopping_list')
