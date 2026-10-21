"""20260617_shopping_line_preferred_buy

FU-215 (PROPOSAL_PRODUCTS_AS_OVERLAY §3.1) — `ShoppingListLine.preferred_buy_id`:
an optional hint pointing at one of the stock item's PreferredBuy labels.

Plain nullable UUID, **no FK constraint** — adding an FK to `ShoppingListLine`
in SQLite batch mode is the FU-178 breakage; SQLite doesn't enforce FKs anyway
and a dangling id is tolerated (the SPA just shows no hint). Reversible.

Revision ID: c4e6a8b1d3f5
Revises: b3d5f7a9c2e4
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

revision = 'c4e6a8b1d3f5'
down_revision = 'b3d5f7a9c2e4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ShoppingListLine') as batch_op:
        batch_op.add_column(
            sa.Column('preferred_buy_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('ShoppingListLine') as batch_op:
        batch_op.drop_column('preferred_buy_id')
