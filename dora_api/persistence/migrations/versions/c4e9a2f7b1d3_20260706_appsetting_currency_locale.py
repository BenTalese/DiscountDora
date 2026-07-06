"""20260706_appsetting_currency_locale

FU-043 (PROPOSAL_LOCALE_I18N Layer A) — add ``currency`` (ISO 4217) and
``locale`` (BCP-47) to the singleton ``AppSetting`` row so a non-AU install
can flip money rendering to its own currency/locale. See
``docs/04_proposals/PROPOSAL_LOCALE_I18N.md``.

Household-scoped by design (one currency per install, not per user) — the
user chose install-wide over per-user during the FU-043 approval pass. If
Dora ever goes multi-tenant SaaS with separate households sharing an
install, this moves onto whatever household row lands then; today, one
value each is correct.

Defaults are Dora's shipping AU defaults (``AUD`` + ``en-AU``), so every
existing install keeps rendering money exactly as it did pre-migration.

Revision ID: c4e9a2f7b1d3
Revises: b7d2f9c1e4a3
Create Date: 2026-07-06 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'c4e9a2f7b1d3'
down_revision = 'b7d2f9c1e4a3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column('currency', sa.String(3), nullable=False, server_default="AUD"))
        batch.add_column(sa.Column('locale', sa.String(35), nullable=False, server_default="en-AU"))


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('locale')
        batch.drop_column('currency')
