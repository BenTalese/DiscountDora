"""20260804_appsetting_product_search_hidden

Add `AppSetting.product_search_hidden`. Lets an operator suppress the
"Product Search" nav entry entirely, independently of whether a URL is set.

Revision ID: a1b7f4e9c3d5
Revises: d3f8b1a6c4e2
Create Date: 2026-08-04 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'a1b7f4e9c3d5'
down_revision = 'd3f8b1a6c4e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(
            sa.Column('product_search_hidden', sa.Boolean(),
                      nullable=False, server_default=sa.false()),
        )


def downgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('product_search_hidden')
