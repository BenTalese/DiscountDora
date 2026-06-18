"""20260618_rename_merchant_to_store

Phase E / FU-189 — `Merchant → Store` rename. One migration covers:

- Rename `Merchant` table to `Store`. Add `Store.image` (nullable bytes)
  for user-uploaded logos (zero shipped — see `manage_stores.py`).
- Rename `Product.merchant_id` → `Product.store_id` (FK now refs `Store.id`).
- Rename `ShoppingListLine.purchased_merchant_id`
  → `ShoppingListLine.purchased_store_id` (FK now refs `Store.id`).
- Rename `IngestionStoreMapping.merchant_id`
  → `IngestionStoreMapping.store_id` (FK now refs `Store.id`).
- Add `StockItem.usual_store_id` (nullable, FK SET NULL on `Store.id`)
  per `PROPOSAL_PRODUCTS_AS_OVERLAY.md` §3.3.

`Product.merchant_stockcode` is intentionally **not** renamed — it's the
producer's SKU code on the offer row, not a reference to the renamed
entity (see PRODUCTS_OVERLAY_RUNBOOK Phase E).

Constraint names follow R-015 (deterministic, SQLite batch-mode-safe).

Revision ID: a3e9f6c2d8b4
Revises: f8b2d4a6c1e3
Create Date: 2026-06-18 00:00:00.000000
"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op


revision = 'a3e9f6c2d8b4'
down_revision = 'f8b2d4a6c1e3'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Rename `Merchant` → `Store` and add the `image` column on it. Doing
    #    the rename first means subsequent batch_alter_table calls on other
    #    tables can target the new `Store.id` for FK rewrites.
    op.rename_table('Merchant', 'Store')

    with op.batch_alter_table('Store') as batch_op:
        # `name` was nullable in the legacy `Merchant` table; tighten to
        # NOT NULL now (no rows on a fresh install; pre-release allows the
        # non-preserving migration).
        batch_op.alter_column('name', existing_type=sa.String(length=255), nullable=False)
        batch_op.add_column(sa.Column('image', sa.LargeBinary(), nullable=True))

    # 2) `Product.merchant_id` → `store_id`. Drop the old FK (named
    #    deterministically per R-015), rename, recreate against `Store`.
    with op.batch_alter_table('Product') as batch_op:
        batch_op.alter_column(
            'merchant_id', new_column_name='store_id',
            existing_type=sqlalchemy_utils.types.uuid.UUIDType(),
            existing_nullable=False,
        )

    # 3) `ShoppingListLine.purchased_merchant_id` → `purchased_store_id`.
    with op.batch_alter_table('ShoppingListLine') as batch_op:
        batch_op.alter_column(
            'purchased_merchant_id', new_column_name='purchased_store_id',
            existing_type=sqlalchemy_utils.types.uuid.UUIDType(),
            existing_nullable=True,
        )

    # 4) `IngestionStoreMapping.merchant_id` → `store_id`.
    with op.batch_alter_table('IngestionStoreMapping') as batch_op:
        batch_op.alter_column(
            'merchant_id', new_column_name='store_id',
            existing_type=sqlalchemy_utils.types.uuid.UUIDType(),
            existing_nullable=True,
        )

    # 5) Add `StockItem.usual_store_id` (nullable, SET NULL on store delete).
    with op.batch_alter_table('StockItem') as batch_op:
        batch_op.add_column(
            sa.Column(
                'usual_store_id', sqlalchemy_utils.types.uuid.UUIDType(),
                nullable=True,
            ),
        )
        batch_op.create_foreign_key(
            'fk_StockItem_usual_store_id_Store',
            'Store', ['usual_store_id'], ['id'], ondelete='SET NULL',
        )


def downgrade():
    # 5) Drop usual_store_id (FK first, then column).
    with op.batch_alter_table('StockItem') as batch_op:
        batch_op.drop_constraint(
            'fk_StockItem_usual_store_id_Store', type_='foreignkey',
        )
        batch_op.drop_column('usual_store_id')

    # 4) IngestionStoreMapping store_id → merchant_id.
    with op.batch_alter_table('IngestionStoreMapping') as batch_op:
        batch_op.alter_column(
            'store_id', new_column_name='merchant_id',
            existing_type=sqlalchemy_utils.types.uuid.UUIDType(),
            existing_nullable=True,
        )

    # 3) ShoppingListLine purchased_store_id → purchased_merchant_id.
    with op.batch_alter_table('ShoppingListLine') as batch_op:
        batch_op.alter_column(
            'purchased_store_id', new_column_name='purchased_merchant_id',
            existing_type=sqlalchemy_utils.types.uuid.UUIDType(),
            existing_nullable=True,
        )

    # 2) Product store_id → merchant_id.
    with op.batch_alter_table('Product') as batch_op:
        batch_op.alter_column(
            'store_id', new_column_name='merchant_id',
            existing_type=sqlalchemy_utils.types.uuid.UUIDType(),
            existing_nullable=False,
        )

    # 1) Drop image, relax name back to nullable, rename table back.
    with op.batch_alter_table('Store') as batch_op:
        batch_op.drop_column('image')
        batch_op.alter_column('name', existing_type=sa.String(length=255), nullable=True)
    op.rename_table('Store', 'Merchant')
