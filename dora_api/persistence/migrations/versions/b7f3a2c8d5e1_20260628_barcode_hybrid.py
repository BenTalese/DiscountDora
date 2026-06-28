"""20260628_barcode_hybrid

FU-056 — convert `ProductBarcode` into the hybrid `Barcode` table.

Rationale (see DORA_FOLLOWUPS_RESOLVED FU-056): EAN scanning needs to
work on installs that don't use the Products overlay too. The shape:

  Barcode {
    id, barcode UNIQUE, created_at,
    product_id NULL UNIQUE FK→Product,
    stock_item_id NULL FK→StockItem,
    CHECK (product_id IS NOT NULL OR stock_item_id IS NOT NULL),
  }

* `product_id` UNIQUE enforces the "one Product = one EAN" rule
  (uniqueness over multi-NULL is supported by both SQLite and Postgres
  — every NULL is treated as distinct).
* `stock_item_id` is not unique → a stock item can carry many direct
  EANs (one per linked Product, plus any user-registered direct ones).
* CHECK prevents orphan rows.

Pre-release — no data preservation needed (the prior table is unused
in any deployed install).

Revision ID: b7f3a2c8d5e1
Revises: a1c5e7d4f2b9
Create Date: 2026-06-28 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

revision = 'b7f3a2c8d5e1'
down_revision = 'a1c5e7d4f2b9'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Add the new columns nullable.
    with op.batch_alter_table('ProductBarcode') as batch:
        batch.add_column(sa.Column(
            'stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(),
            sa.ForeignKey('StockItem.id', ondelete='CASCADE'),
            nullable=True,
        ))
        batch.add_column(sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=True,
        ))
    # 2) Backfill created_at on any existing rows.
    op.execute(
        'UPDATE "ProductBarcode" SET created_at = CURRENT_TIMESTAMP '
        'WHERE created_at IS NULL'
    )
    # 3) Tighten created_at; relax product_id; add UNIQUE + CHECK.
    with op.batch_alter_table('ProductBarcode') as batch:
        batch.alter_column('created_at', nullable=False)
        batch.alter_column('product_id', nullable=True)
        batch.create_unique_constraint('uq_barcode_product_id', ['product_id'])
        batch.create_check_constraint(
            'ck_barcode_target_at_least_one',
            'product_id IS NOT NULL OR stock_item_id IS NOT NULL',
        )
    # 4) Rename to the truer name now that it's no longer Product-only.
    op.rename_table('ProductBarcode', 'Barcode')


def downgrade():
    op.rename_table('Barcode', 'ProductBarcode')
    with op.batch_alter_table('ProductBarcode') as batch:
        batch.drop_constraint('ck_barcode_target_at_least_one', type_='check')
        batch.drop_constraint('uq_barcode_product_id', type_='unique')
        batch.alter_column('product_id', nullable=False)
        batch.drop_column('created_at')
        batch.drop_column('stock_item_id')
