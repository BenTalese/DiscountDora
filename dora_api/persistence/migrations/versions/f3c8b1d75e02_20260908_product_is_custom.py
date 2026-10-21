"""20260908_product_is_custom

OD-2 — hand-entered ("custom") products, for shops no scraper covers.

`PreferredBuy` was meant to be the everyday substitute, but it is a *label*:
no price, no store, no history. So a user wanting to record "the butcher's
mince is $12/kg" had to choose between a note they could not compare and a
product they could not create. `Product.is_custom` marks the ones they type
themselves.

The flag is load-bearing rather than cosmetic:

- **The scheduled sync must skip them.** There is nothing to refresh a custom
  product *from*, and asking a provider to find it would at best waste a
  request and at worst match something else.
- **Ingestion must not adopt them.** `submit_ingestion_batch` dedupes on
  `(store, name)` when a pushed record has no stockcode, so without this a
  scraped "Mince" would match a hand-entered "Mince" at the same store and
  overwrite its brand, size and price — silently turning the user's own figure
  into scraped data, which is the kind of quiet substitution the products
  program spent its whole time removing.

Forward-only, defaulted `False`: every existing product came from ingestion.

Revision ID: f3c8b1d75e02
Revises: e7a2c4f9b361
Create Date: 2026-09-08 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'f3c8b1d75e02'
down_revision = 'e7a2c4f9b361'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'Product',
        sa.Column(
            'is_custom', sa.Boolean(), nullable=False, server_default=sa.false(),
        ),
    )


def downgrade():
    op.drop_column('Product', 'is_custom')
