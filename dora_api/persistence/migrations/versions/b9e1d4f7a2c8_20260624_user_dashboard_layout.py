"""20260624_user_dashboard_layout

Add `dashboard_layout` to the User table — a small JSON string holding the
user's dashboard card order + hidden set (Dashboard rebuild Phase 2). NULL =
not customised; the SPA falls back to the default layout. Opaque client
view-state, persisted so it survives a cache clear and follows the user across
devices. Text for Postgres/SQLite portability; batch mode for SQLite.

Revision ID: b9e1d4f7a2c8
Revises: c2e9f4a6b8d3
Create Date: 2026-06-24 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'b9e1d4f7a2c8'
down_revision = 'c2e9f4a6b8d3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column('dashboard_layout', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('dashboard_layout')
