"""20260703_user_inferred_pantry

P8-07 (Zero-Input Pantry) — per-user opt-out for inferred stock levels.
Default TRUE: inference is the headline experience (Charter 1 — the app
works for you), but Charter 10 says some users want purely manual control,
so a Preferences toggle can switch the belief overlay off.

`server_default=true()` so existing rows adopt inference on upgrade.
Same shape as the `show_stock_images` opt-in (d4a7c9b3e8f1).

Revision ID: a3e8b1f6c2d9
Revises: f2a9c4d7e1b8
Create Date: 2026-07-03 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import true

revision = 'a3e8b1f6c2d9'
down_revision = 'f2a9c4d7e1b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column(
            'inferred_pantry_enabled', sa.Boolean(),
            nullable=False, server_default=true(),
        ))


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('inferred_pantry_enabled')
