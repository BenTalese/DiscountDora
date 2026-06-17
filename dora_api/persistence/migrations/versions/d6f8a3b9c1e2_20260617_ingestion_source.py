"""20260617_ingestion_source

C-10.1 (PROPOSAL_INGESTION_API §2.1) — `IngestionSource`: admin-minted
bearer credential the external producer authenticates with when pushing
to `POST /api/ingest`. The raw key is shown once at creation; only its
SHA-256 hash lives at rest (mirrors `AuthToken.token_hash`). Counters +
`last_used_at` are the observability feed for the API access page
(C-10.3). `trust` is captured per §2.6; enforcement is deferred.

Revision ID: d6f8a3b9c1e2
Revises: c4e6a8b1d3f5
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'd6f8a3b9c1e2'
down_revision = 'c4e6a8b1d3f5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'IngestionSource',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('trust', sa.String(length=16), nullable=False, server_default='high'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accepted_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('key_hash', name='uq_ingestion_source_key_hash'),
    )


def downgrade():
    op.drop_table('IngestionSource')
