"""20260611_user_money_optin

C-cross Chunk 2 — per-user money-features opt-in (proposal §2.2).

Adds `User.money_features_enabled bool` (default False, per Charter P10
Anti-creep). Layered with the install-wide `AppSetting.money_enabled`
(Chunk 1) — both must be true for any dollar surface to render.

Existing `budget_amount` / `budget_period` columns stay where they are.
A user who turns money features off keeps their saved budget value;
toggling back on restores it untouched.

Revision ID: b5c1d9a4e3f2
Revises: a3b8e2f4c1d7
Create Date: 2026-06-11 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'b5c1d9a4e3f2'
down_revision = 'a3b8e2f4c1d7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column('money_features_enabled', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('money_features_enabled')
