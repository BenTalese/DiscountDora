"""20260707_auto_add_mode

FU-511 — collapse per-item ``StockItem.auto_add_when_low`` into a single
install-wide setting ``AppSetting.auto_add_mode``. Values:
``'off'`` / ``'essential_only'`` (default) / ``'all'``.

Rationale: auto-add was already conceptually coupled to Essential (the
detail-page tooltip literally read "Use for essentials you never want to
run out of"). The per-item boolean was redundant with ``is_flagged`` for
almost every real user; collapsing it removes a column, an API field, a
filter chip, a footer count, a detail-page toggle, and the spreadsheet-
import column, and reduces the "set up an item" surface.

Pre-release breaking-changes-OK posture — the drop is unconditional and
non-preserving. Any install that had per-item toggles will fall back to
``essential_only`` (auto-add fires for items with ``is_flagged=True``);
that's the closest single behaviour to the previous per-item pattern.

Schema changes:
1. Add ``AppSetting.auto_add_mode`` (String(16), NOT NULL, server_default
   ``'essential_only'``).
2. Drop ``StockItem.auto_add_when_low``.

Revision ID: b8f2c1d4e6a9
Revises: a4c9e1f2b3d5
Create Date: 2026-07-07 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'b8f2c1d4e6a9'
down_revision = 'a4c9e1f2b3d5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'auto_add_mode', sa.String(length=16),
            nullable=False, server_default='essential_only',
        ))
    with op.batch_alter_table('StockItem') as batch:
        batch.drop_column('auto_add_when_low')


def downgrade():
    with op.batch_alter_table('StockItem') as batch:
        batch.add_column(sa.Column(
            'auto_add_when_low', sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ))
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('auto_add_mode')
