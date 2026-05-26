"""20260530_shopping_list_line_added_via

Adds ShoppingListLine.added_via + added_at — provenance of how each
line landed on the list (manual user add, /auto-generate from low
stock / essentials / flagged / recipe / meal plan / frequently added,
or the auto_add_when_low trigger).

The UI renders a chip on each line when added_via != "manual" so the
user can see "this jumped onto your list because it dropped to low
stock". added_at backs sort-by-newest and the undoable notification
window for the auto_add_when_low trigger.

Revision ID: b5d8e2f3c14a
Revises: a4c7e1d9b832
Create Date: 2026-05-30 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'b5d8e2f3c14a'
down_revision = 'a4c7e1d9b832'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingListLine') as batch:
        batch.add_column(
            sa.Column('added_via', sa.String(length=32),
                      nullable=False, server_default='manual')
        )
        batch.add_column(
            sa.Column('added_at', sa.DateTime(timezone=True), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('ShoppingListLine') as batch:
        batch.drop_column('added_at')
        batch.drop_column('added_via')
