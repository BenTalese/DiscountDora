"""20260617_drop_appsetting_products_enabled

FU-209 (PROPOSAL_PRODUCTS_AS_OVERLAY) — products is now a **data-presence**
overlay: `features.products` is derived server-side from whether any `Product`
row exists (see health_check), not from an admin/persona flag. The
`AppSetting.products_enabled` column added by d1f4b8c3e7a9 is therefore unused;
drop it.

Pre-release — no data preservation needed (clean, non-preserving migration is
allowed). Reversible, batch-mode for SQLite portability (R-005/R-006), no
idempotent guards.

Revision ID: f1a2b3c4d5e6
Revises: e9a4b6c2d8f1
Create Date: 2026-06-17 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'f1a2b3c4d5e6'
down_revision = 'e9a4b6c2d8f1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('products_enabled')


def downgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(
            sa.Column('products_enabled', sa.Boolean(), nullable=False, server_default='1')
        )
