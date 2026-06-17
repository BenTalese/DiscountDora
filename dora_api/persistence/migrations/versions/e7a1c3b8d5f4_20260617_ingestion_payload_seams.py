"""20260617_ingestion_payload_seams

C-10.2 (PROPOSAL_INGESTION_API §2.2-§2.4 + FU-190):
- `ProductHistoricOffer.source` — provenance string on every historic
  point (nullable; legacy rows from `create_product` pre-C-10 won't
  have one).
- `IdempotencyKey` — consumed `Idempotency-Key`s from `POST /api/ingest`,
  so a re-send is a no-op until the TTL passes.
- `IngestionStoreMapping` — per-source external-name → Merchant mapping
  (FU-190: no auto-create stores; unknown names quarantine).

Revision ID: e7a1c3b8d5f4
Revises: d6f8a3b9c1e2
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'e7a1c3b8d5f4'
down_revision = 'd6f8a3b9c1e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ProductHistoricOffer') as batch_op:
        batch_op.add_column(sa.Column('source', sa.String(length=64), nullable=True))

    op.create_table(
        'IdempotencyKey',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    # Hot lookup on resend: "have I seen (key, source) before?" — index
    # both columns together.
    op.create_index(
        'ix_idempotency_key_source_key',
        'IdempotencyKey',
        ['source_id', 'key'],
        unique=True,
    )

    op.create_table(
        'IngestionStoreMapping',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('source_id', UUIDType,
                  sa.ForeignKey('IngestionSource.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('external_name', sa.String(length=255), nullable=False),
        sa.Column('merchant_id', UUIDType,
                  sa.ForeignKey('Merchant.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('source_id', 'external_name',
                            name='uq_ingestion_store_mapping_source_external'),
    )


def downgrade():
    op.drop_table('IngestionStoreMapping')
    op.drop_index('ix_idempotency_key_source_key', table_name='IdempotencyKey')
    op.drop_table('IdempotencyKey')
    with op.batch_alter_table('ProductHistoricOffer') as batch_op:
        batch_op.drop_column('source')
