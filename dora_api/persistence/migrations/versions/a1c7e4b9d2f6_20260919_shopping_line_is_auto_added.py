"""20260919_shopping_line_is_auto_added

Replaces `ShoppingListLine.added_via` (a 7-value provenance string) with
`is_auto_added` (bool).

The enum existed to render a per-row "auto: low stock" / "auto: recipe X"
caption. Six of its seven values described *which auto-generate source*
produced a line — but the user picks those sources in the New list dialog
seconds earlier, so the caption restated their own input back at them on
every row, forever. The one distinction worth keeping is "did a user action
put this here, or did it appear as a knock-on of a stock level changing",
which is a boolean.

Old values map as:

    auto_low_stock written by the update_stock_item hook -> True
    everything else                                      -> False

That mapping can't be made faithfully in SQL: `auto_low_stock` was written
by *both* the stock-level hook and the auto-generate collector, and nothing
in the row distinguishes them. Pre-release, so historical rows collapse to
False rather than carrying a guess forward — the marker is a "you didn't do
this" hint on a live list, and a wrong one is worse than none.
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1c7e4b9d2f6'
down_revision = 'f3c8b1d75e02'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingListLine') as batch:
        batch.add_column(sa.Column(
            'is_auto_added', sa.Boolean(), nullable=False,
            server_default=sa.false(),
        ))
        batch.drop_column('added_via')


def downgrade():
    with op.batch_alter_table('ShoppingListLine') as batch:
        batch.add_column(sa.Column(
            'added_via', sa.String(32), nullable=False,
            server_default='manual',
        ))
        batch.drop_column('is_auto_added')
