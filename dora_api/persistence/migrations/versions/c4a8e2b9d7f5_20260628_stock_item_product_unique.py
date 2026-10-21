"""20260628_stock_item_product_unique

FU-056 — enforce "one Product = one StockItem" in the StockItemProduct
join table by adding `UNIQUE(product_id)`. The relation stays m:n in
shape (many Products on one StockItem is legitimate — Coles + Pauls +
Vitasoy all satisfy a "Milk" pantry slot), but the asymmetric truth
locked down here is: a Product satisfies exactly one StockItem.

Eliminates the `product_multi_linked` lookup-result kind from
`barcode_lookup` (and the dialog branches that handled it) — the
ambiguity was a data-shape accident, not a real configuration.

Pre-release — no backfill needed (seed already conforms; verified).
SQLite supports table-level UNIQUE via batch-mode rebuild; Postgres
handles it natively.

Revision ID: c4a8e2b9d7f5
Revises: b7f3a2c8d5e1
Create Date: 2026-06-28 00:00:00.000000

"""
from alembic import op

revision = 'c4a8e2b9d7f5'
down_revision = 'b7f3a2c8d5e1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItemProduct') as batch:
        batch.create_unique_constraint(
            'uq_stock_item_product_product_id',
            ['product_id'],
        )


def downgrade():
    with op.batch_alter_table('StockItemProduct') as batch:
        batch.drop_constraint(
            'uq_stock_item_product_product_id',
            type_='unique',
        )
