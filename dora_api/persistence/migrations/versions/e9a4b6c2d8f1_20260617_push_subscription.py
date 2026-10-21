"""20260617_push_subscription

C-9.8 — Web-push subscription registry. One row per browser+device push
registration (PROPOSAL_ALERTS §4.4): the vendor-issued `endpoint` URL is
the natural key (re-subscribes from the same browser produce the same
endpoint), and the `p256dh`/`auth` pair is the per-subscription key
material the backend needs to ECE-encrypt payloads only that browser can
read. `user_agent` is captured so the (future) per-device list in
Preferences can name the row "Chrome on Linux" / "Firefox on Android".

Revision ID: e9a4b6c2d8f1
Revises: d7b3e2a1f4c5
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'e9a4b6c2d8f1'
down_revision = 'd7b3e2a1f4c5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'PushSubscription',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('user_id', UUIDType, nullable=False),
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('p256dh', sa.String(length=255), nullable=False),
        sa.Column('auth', sa.String(length=64), nullable=False),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('endpoint', name='uq_push_subscription_endpoint'),
    )
    # Hot query: "which subscriptions belong to user X" (the push job
    # fans out per-user). Indexing keeps that bounded as devices stack up.
    op.create_index(
        'ix_push_subscription_user_id',
        'PushSubscription',
        ['user_id'],
    )


def downgrade():
    op.drop_index('ix_push_subscription_user_id', table_name='PushSubscription')
    op.drop_table('PushSubscription')
