"""20260622_pack_count_locale

FU-227 follow-up — multipack support + US locale switch.

Adds three columns:

- ``Product.pack_count INTEGER NULL`` — how many individual packs/items the
  product's ``size_value`` represents (e.g. 4 for "125g × 4 pack"). NULL =
  single pack / free-weight, the common case. Informational only — the
  per-unit math stays ``total_price / size_value`` and ``size_value``
  remains the TOTAL across the bundle (existing convention preserved so
  every seeded / ingested row stays correct without a backfill).
- ``StockItemPriceObservation.pack_count INTEGER NULL`` — same semantics
  on the user's observation row. Lets the obs list render "4 × 125g"
  instead of "500g flat" while keeping math identical.
- ``AppSetting.unit_pricing_locale VARCHAR(8) NOT NULL DEFAULT 'AU'`` —
  switches the per-unit *display* denominator between AU shelf convention
  (``/100ml`` / ``/100g`` / ``/L`` / ``/kg``) and US (``/fl oz`` / ``/oz``
  / ``/qt`` / ``/lb``). Compute math is locale-independent — only the
  rendered denominator changes — so this is a pure-display switch.

Postgres + SQLite both support ``ADD COLUMN ... NULL`` without a rewrite,
so this is a cheap migration. Server-default for the new locale column so
existing AppSetting rows pick up ``'AU'`` automatically.

Revision ID: d7b3e8f2a5c4
Revises: c6e9a4b8d5f2
Create Date: 2026-06-22 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'd7b3e8f2a5c4'
down_revision = 'c6e9a4b8d5f2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Product') as batch_op:
        batch_op.add_column(
            sa.Column('pack_count', sa.Integer(), nullable=True),
        )
    with op.batch_alter_table('StockItemPriceObservation') as batch_op:
        batch_op.add_column(
            sa.Column('pack_count', sa.Integer(), nullable=True),
        )
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(
            sa.Column(
                'unit_pricing_locale',
                sa.String(length=8),
                nullable=False,
                server_default='AU',
            ),
        )


def downgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('unit_pricing_locale')
    with op.batch_alter_table('StockItemPriceObservation') as batch_op:
        batch_op.drop_column('pack_count')
    with op.batch_alter_table('Product') as batch_op:
        batch_op.drop_column('pack_count')
