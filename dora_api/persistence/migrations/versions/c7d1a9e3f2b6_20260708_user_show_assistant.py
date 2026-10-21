"""20260708_user_show_assistant

FU-360.6 — per-user opt-out for the Dora helper bubble. Adds
``User.show_assistant`` (Boolean, NOT NULL, server_default TRUE). When a
user flips it off, the SPA never mounts the assistant launcher — both Basic
and AI mode disappear for them. Distinct from ``User.llm_enabled`` (which
only switches the AI *mode*).

Default TRUE keeps every existing user's bubble visible (Charter P1
Effortless — discoverable by default); opting out is a deliberate act.

Revision ID: c7d1a9e3f2b6
Revises: b8f2c1d4e6a9
Create Date: 2026-07-08 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'c7d1a9e3f2b6'
down_revision = 'b8f2c1d4e6a9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'show_assistant', sa.Boolean(),
            nullable=False, server_default=sa.true(),
        ))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('show_assistant')
