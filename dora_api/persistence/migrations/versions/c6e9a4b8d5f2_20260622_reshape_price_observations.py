"""20260622_reshape_price_observations

FU-227 chunk 2 — reshape `StockItemPriceObservation` to the folded
`{total_price, total_measure, unit}` shape (A1), add nullable `store_id` (A2)
and nullable `shopping_list_line_id` FK (A4 revised) replacing the old `source`
enum, and add a partial UNIQUE index on `shopping_list_line_id WHERE NOT NULL`
(LC-1) so `/finish` harvest is idempotent under finish-button double-taps.

**Non-preserving** per K1 (pre-release, dev-only data; the rule is documented
in user memory `feedback_migrations_schema.md` — destructive resets use
`DORA_ALLOW_DESTRUCTIVE` drop_all, no idempotent guards). The old free-text
`unit` field meant existing rows couldn't be migrated forward without a
manual triage anyway. Down-migration restores the old shape with the same
non-preserving semantics.

Revision ID: c6e9a4b8d5f2
Revises: b5d8a2f4c9e7
Create Date: 2026-06-22 00:00:00.000000
"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op


revision = 'c6e9a4b8d5f2'
down_revision = 'b5d8a2f4c9e7'
branch_labels = None
depends_on = None


def upgrade():
    # K1: drop + recreate. Non-preserving because the old `unit` field was
    # free-text (50 chars) and can't be safely auto-coerced to the supported
    # set; rebuilding from seed is the documented dev workflow.
    op.drop_table('StockItemPriceObservation')
    op.create_table(
        'StockItemPriceObservation',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('total_measure', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=32), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('store_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        sa.Column('shopping_list_line_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['stock_item_id'], ['StockItem.id'],
            name='fk_stock_item_price_observation_stock_item_id',
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['store_id'], ['Store.id'],
            name='fk_stock_item_price_observation_store_id',
            ondelete='SET NULL',
        ),
        sa.ForeignKeyConstraint(
            ['shopping_list_line_id'], ['ShoppingListLine.id'],
            name='fk_stock_item_price_observation_shopping_list_line_id',
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id', name='pk_stock_item_price_observation'),
    )

    # LC-1 — partial UNIQUE: at most one observation per line. Postgres and
    # SQLite (>= 3.8) both support partial indexes with this syntax. Naming
    # the index makes it dropable via batch-mode on SQLite (R-015).
    op.create_index(
        'uq_stock_item_price_observation_shopping_list_line_id',
        'StockItemPriceObservation',
        ['shopping_list_line_id'],
        unique=True,
        sqlite_where=sa.text('shopping_list_line_id IS NOT NULL'),
        postgresql_where=sa.text('shopping_list_line_id IS NOT NULL'),
    )


def downgrade():
    # Mirror of upgrade — drops the new shape + index, restores the old
    # (FU-213-era) shape so the chain can roll back. Existing reshaped rows
    # are lost in both directions; documented above.
    op.drop_index(
        'uq_stock_item_price_observation_shopping_list_line_id',
        table_name='StockItemPriceObservation',
    )
    op.drop_table('StockItemPriceObservation')
    op.create_table(
        'StockItemPriceObservation',
        sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['stock_item_id'], ['StockItem.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
