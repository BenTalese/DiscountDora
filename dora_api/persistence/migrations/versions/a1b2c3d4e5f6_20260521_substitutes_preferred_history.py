"""20260521_substitutes_preferred_history

Stock-item detail "hub" schema (P2):

  StockItemSubstitute   — self-referential m2m; row (A, B) = "B substitutes A"
  StockItem.preferred_product_id — FK to the preferred linked Product
  StockLevelChange      — append-only log of level transitions

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-05-21 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_column(table: str, column: str) -> bool:
    return any(c['name'] == column for c in sa.inspect(op.get_bind()).get_columns(table))


def upgrade():
    # Guarded so this is safe whether or not `db.create_all()` (the dev-mode
    # path) already materialised these tables/columns from the ORM metadata.
    if not _has_table('StockItemSubstitute'):
        op.create_table(
            'StockItemSubstitute',
            sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
            sa.Column('substitute_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
            sa.ForeignKeyConstraint(['stock_item_id'], ['StockItem.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['substitute_id'], ['StockItem.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('stock_item_id', 'substitute_id'),
        )

    if not _has_table('StockLevelChange'):
        op.create_table(
            'StockLevelChange',
            sa.Column('id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
            sa.Column('stock_item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
            sa.Column('stock_level_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
            sa.Column('stock_level_name', sa.String(length=255), nullable=True),
            sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['stock_item_id'], ['StockItem.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['stock_level_id'], ['StockLevel.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )

    if not _has_column('StockItem', 'preferred_product_id'):
        with op.batch_alter_table('StockItem') as batch:
            batch.add_column(sa.Column(
                'preferred_product_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True
            ))
            batch.create_foreign_key(
                'fk_StockItem_preferred_product_id_Product',
                'Product', ['preferred_product_id'], ['id'], ondelete='SET NULL',
            )


def downgrade():
    if _has_column('StockItem', 'preferred_product_id'):
        # Dropping the column in batch mode recreates the table without it,
        # taking the FK with it — no explicit drop_constraint (SQLite doesn't
        # name FKs).
        with op.batch_alter_table('StockItem') as batch:
            batch.drop_column('preferred_product_id')
    if _has_table('StockLevelChange'):
        op.drop_table('StockLevelChange')
    if _has_table('StockItemSubstitute'):
        op.drop_table('StockItemSubstitute')
