"""20260627_substitute_notes_ratio

FU-034 — wire `StockItemSubstitute.notes` (already existed as an unused
column) and add an optional structured **ratio** so the substitute pair
can carry both a free-text hint ("don't use in baking", "1:1 swap") and
a parseable "X of A → Y of B" relationship for the cook-mode picker to
display.

The four ratio columns are **all-or-none** — the CHECK constraint forbids
half-filled ratios. Storage is directional in the **canonical** pair's
A→B direction (the schema's `(a_id < b_id)` rule). The
`get_stock_item_detail` handler inverts the ratio at read time so the
viewer sees `qty_in/unit_in` referring to the item they're looking at.

Pre-release — no data preservation needed; existing `notes` rows are
already all NULL (the wire-up was deferred at column-add time).

Revision ID: a1c5e7d4f2b9
Revises: f9d3a7c2b5e8
Create Date: 2026-06-27 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'a1c5e7d4f2b9'
down_revision = 'f9d3a7c2b5e8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('StockItemSubstitute') as batch:
        batch.add_column(sa.Column('ratio_quantity_in', sa.Float(), nullable=True))
        batch.add_column(sa.Column('ratio_unit_in', sa.String(length=32), nullable=True))
        batch.add_column(sa.Column('ratio_quantity_out', sa.Float(), nullable=True))
        batch.add_column(sa.Column('ratio_unit_out', sa.String(length=32), nullable=True))
        batch.create_check_constraint(
            'ck_substitute_ratio_all_or_none',
            '(ratio_quantity_in IS NULL AND ratio_unit_in IS NULL '
            ' AND ratio_quantity_out IS NULL AND ratio_unit_out IS NULL) '
            'OR (ratio_quantity_in IS NOT NULL AND ratio_unit_in IS NOT NULL '
            ' AND ratio_quantity_out IS NOT NULL AND ratio_unit_out IS NOT NULL)',
        )


def downgrade():
    with op.batch_alter_table('StockItemSubstitute') as batch:
        batch.drop_constraint('ck_substitute_ratio_all_or_none', type_='check')
        batch.drop_column('ratio_unit_out')
        batch.drop_column('ratio_quantity_out')
        batch.drop_column('ratio_unit_in')
        batch.drop_column('ratio_quantity_in')
