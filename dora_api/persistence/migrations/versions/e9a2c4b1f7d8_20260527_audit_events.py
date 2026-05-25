"""20260527_audit_events

Adds the audit_events table used by I2's audit log + the admin UI that
sits on top of it. Schema mirrors the brief: occurred_at + actor +
action + entity ref + request_id + payload JSON + severity.

Indexes are tuned for the four real query shapes the admin UI exposes:
recent (occurred_at), per-user history (actor_user_id, occurred_at),
per-entity history (entity_type, entity_id, occurred_at), and
per-action filter (action, occurred_at).

Revision ID: e9a2c4b1f7d8
Revises: d7f4a2c98e15
Create Date: 2026-05-27 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

# revision identifiers, used by Alembic.
revision = 'e9a2c4b1f7d8'
down_revision = 'd7f4a2c98e15'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'AuditEvent',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(16), nullable=False),
        sa.Column('actor_user_id', UUIDType, nullable=True),
        sa.Column('actor_ip', sa.String(64), nullable=True),
        sa.Column('action', sa.String(128), nullable=False),
        sa.Column('entity_type', sa.String(64), nullable=True),
        sa.Column('entity_id', UUIDType, nullable=True),
        sa.Column('request_id', sa.String(64), nullable=True),
        sa.Column('payload', sa.Text, nullable=True),   # JSON-encoded
        sa.Column('severity', sa.String(16), nullable=False),
    )
    op.create_index('ix_AuditEvent_occurred_at', 'AuditEvent', ['occurred_at'])
    op.create_index(
        'ix_AuditEvent_actor_occurred', 'AuditEvent',
        ['actor_user_id', 'occurred_at'],
    )
    op.create_index(
        'ix_AuditEvent_entity_occurred', 'AuditEvent',
        ['entity_type', 'entity_id', 'occurred_at'],
    )
    op.create_index(
        'ix_AuditEvent_action_occurred', 'AuditEvent',
        ['action', 'occurred_at'],
    )


def downgrade():
    op.drop_index('ix_AuditEvent_action_occurred', table_name='AuditEvent')
    op.drop_index('ix_AuditEvent_entity_occurred', table_name='AuditEvent')
    op.drop_index('ix_AuditEvent_actor_occurred', table_name='AuditEvent')
    op.drop_index('ix_AuditEvent_occurred_at', table_name='AuditEvent')
    op.drop_table('AuditEvent')
