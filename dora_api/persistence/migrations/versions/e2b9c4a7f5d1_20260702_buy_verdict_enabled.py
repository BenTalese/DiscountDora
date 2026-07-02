"""20260702_buy_verdict_enabled

P8-05 — install-wide `AppSetting.buy_verdict_enabled` boolean flag that
gates the "Should I buy this?" oracle. Defaults **true** because the
oracle is a pure-personal feature: no external calls, no crowd data, no
config required. Admins can flip it off from Settings → System if the
row-level badges feel noisy on their pantry.

Revision ID: e2b9c4a7f5d1
Revises: f7a3b8e2c1d5
Create Date: 2026-07-02 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'e2b9c4a7f5d1'
down_revision = 'f7a3b8e2c1d5'
branch_labels = None
depends_on = None


def upgrade():
    # R-005 — batch_alter_table so SQLite recreates the table cleanly.
    # Boolean default `true` uses the same "1" server_default pattern the
    # sibling `meal_planning_enabled` migration used; SQLAlchemy renders
    # the vendor-appropriate literal on both SQLite and Postgres.
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'buy_verdict_enabled', sa.Boolean(),
            nullable=False, server_default=sa.true(),
        ))


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('buy_verdict_enabled')
