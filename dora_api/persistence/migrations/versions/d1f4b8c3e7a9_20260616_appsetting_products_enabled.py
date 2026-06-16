"""20260616_appsetting_products_enabled

Onboarding C-5.3 — the products feature flag (PROPOSAL_ONBOARDING §3.2).

Adds one boolean column to the `AppSetting` singleton row, joining the
C-cross install-flag family (don't duplicate the flag machinery — R-003).

Default **True** so existing installs keep their linked products / price
history / ingestion surfaces; the onboarding "Cooking" persona is what turns
it off. Per-surface hiding when the flag is off is FU-182, not this migration.

Revision ID: d1f4b8c3e7a9
Revises: b1e7d3f9a2c4
Create Date: 2026-06-16 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'd1f4b8c3e7a9'
down_revision = 'b1e7d3f9a2c4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(
            sa.Column('products_enabled', sa.Boolean(), nullable=False, server_default='1')
        )


def downgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('products_enabled')
