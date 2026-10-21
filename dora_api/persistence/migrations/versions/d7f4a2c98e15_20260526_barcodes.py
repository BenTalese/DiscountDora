"""20260526_barcodes

Adds the barcode column on StockItem and a new ProductBarcode table.
Pre-release rules: destructive migration acceptable, but the additions
here are purely additive so existing data survives.

Revision ID: d7f4a2c98e15
Revises: c5e8f3a91b07
Create Date: 2026-05-26 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

# revision identifiers, used by Alembic.
revision = 'd7f4a2c98e15'
down_revision = 'c5e8f3a91b07'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItem') as batch:
        batch.add_column(sa.Column('barcode', sa.String(255), nullable=True))
        batch.create_unique_constraint('uq_StockItem_barcode', ['barcode'])

    op.create_table(
        'ProductBarcode',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column(
            'product_id', UUIDType,
            sa.ForeignKey('Product.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('barcode', sa.String(255), nullable=False, unique=True),
    )


def downgrade():
    op.drop_table('ProductBarcode')
    with op.batch_alter_table('StockItem') as batch:
        batch.drop_constraint('uq_StockItem_barcode', type_='unique')
        batch.drop_column('barcode')
