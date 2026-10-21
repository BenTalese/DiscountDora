"""20260617_appsetting_product_search_url

Phase D / FU-186 — add `AppSetting.product_search_url`. Install-wide URL
the Product Search nav entry opens when product data is present (the
companion / source the admin runs themselves). Empty string ⇒ unset; the
nav entry renders disabled with a "Set up in Settings" hint. The companion
is **never named** anywhere in the UI; the user just sees "Product Search".
See `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §4.1.

Revision ID: f8b2d4a6c1e3
Revises: e7a1c3b8d5f4
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'f8b2d4a6c1e3'
down_revision = 'e7a1c3b8d5f4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(
            sa.Column('product_search_url', sa.String(length=500),
                      nullable=False, server_default=''),
        )


def downgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('product_search_url')
