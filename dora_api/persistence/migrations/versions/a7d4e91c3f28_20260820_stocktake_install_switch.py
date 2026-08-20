"""20260820_stocktake_install_switch

Owner feedback 2026-08-20 (stock overview batch): *"There should be an
install-wide setting for disabling stocktake where the button is hidden on the
overview, and alongside it is the toggle for stocktake opt-in behaviour for new
items (default is opted in). Should also hide the stocktake per-item opt-in
toggle."*

Two new ``AppSetting`` columns, both defaulting TRUE so every existing install
keeps exactly the behaviour it has today:

* ``stocktake_enabled`` — the master switch. FALSE means the feature does not
  exist for this install: the Stock-overview button, the "Needs check" filter,
  the per-item mute toggle and the runner all disappear on the client, and
  ``resolve_overdue_map`` (the single overdue authority, R-003) short-circuits
  to an empty map on the server so the alerts bell can't nag about a surface
  nobody can open. Published to clients as ``/api/health features.stocktake``.
* ``stocktake_new_items_opt_in`` — what ``create_stock_item`` seeds
  ``StockItem.stocktake_alerts_are_enabled`` with. TRUE keeps the 2026-08-17
  default ("an item you bothered to add is one you want checked").

Existing rows are untouched beyond the new columns; nothing about the per-item
flag already stored on ``StockItem`` changes.

Revision ID: a7d4e91c3f28
Revises: c8b3e5f0a712
Create Date: 2026-08-20 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import true

revision = 'a7d4e91c3f28'
down_revision = 'c8b3e5f0a712'
branch_labels = None
depends_on = None


def upgrade():
    # R-005 — batch_alter_table so SQLite recreates the table cleanly.
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'stocktake_enabled', sa.Boolean(),
            nullable=False, server_default=true(),
        ))
        batch.add_column(sa.Column(
            'stocktake_new_items_opt_in', sa.Boolean(),
            nullable=False, server_default=true(),
        ))


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('stocktake_new_items_opt_in')
        batch.drop_column('stocktake_enabled')
