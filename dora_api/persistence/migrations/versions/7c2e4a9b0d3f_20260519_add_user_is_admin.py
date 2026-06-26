"""20260519_add_user_is_admin

Adds the `is_admin` flag to the User table so the web app can gate the
global/admin section of the settings page.

Revision ID: 7c2e4a9b0d3f
Revises: 5c2e8a4f9b1d
Create Date: 2026-05-19 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '7c2e4a9b0d3f'
# Branched off 4b1d9c2e7a31 by mistake; the real head at that time was
# 5c2e8a4f9b1d (link_stock_items_to_products). Re-pointed to keep the
# chain linear.
down_revision = '5c2e8a4f9b1d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(
            sa.Column(
                'is_admin',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('is_admin')
