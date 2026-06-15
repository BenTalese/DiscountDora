"""20260615_alert_interactions

C-9.1 — per-user interaction state for derived alerts: read / snooze /
dismiss decisions, keyed by the alert's stable ``<scope>:<id>:<kind>`` key.
The alerts themselves stay derived (not stored); only the user's decisions
persist. Mirrors the DoraSuggestionSuppression table, with a per-user
``user_id`` + ``read_at`` (read/snooze are inherently per-user).

Revision ID: f4d2a9c7b3e1
Revises: a3c9e7b2f5d8
Create Date: 2026-06-15 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'f4d2a9c7b3e1'
down_revision = 'a3c9e7b2f5d8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'AlertInteraction',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('user_id', UUIDType, nullable=False),
        sa.Column('alert_key', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('snoozed_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
    )
    # The hot query is "this user's interactions for the alerts I just
    # generated" — a composite index keeps the GET overlay cheap as the
    # table grows.
    op.create_index(
        'ix_alert_interaction_user_key',
        'AlertInteraction',
        ['user_id', 'alert_key'],
    )


def downgrade():
    op.drop_index('ix_alert_interaction_user_key', table_name='AlertInteraction')
    op.drop_table('AlertInteraction')
