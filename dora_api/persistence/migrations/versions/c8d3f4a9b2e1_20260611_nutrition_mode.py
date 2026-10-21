"""20260611_nutrition_mode

C-cross Chunk 3 — per-user nutrition mode + reserved complex seam.

Adds:
- `User.nutrition_mode VARCHAR(16)` default `'off'`. Closed-set sentinel
  per R-010 carve-out — validated at the boundary
  (`update_me.py`) against `NUTRITION_MODE_VALUES`. SQLite-portable
  (no CHECK constraint).
- `AppSetting.nutrition_db_source VARCHAR(255)` default `''`. Reserved
  seam for the §2.3 complex-mode integration — no implementation yet;
  the column exists so update_me can refuse `nutrition_mode='complex'`
  writes until an admin configures it.

Revision ID: c8d3f4a9b2e1
Revises: b5c1d9a4e3f2
Create Date: 2026-06-11 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'c8d3f4a9b2e1'
down_revision = 'b5c1d9a4e3f2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(sa.Column('nutrition_mode', sa.String(length=16), nullable=False, server_default='off'))
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(sa.Column('nutrition_db_source', sa.String(length=255), nullable=False, server_default=''))


def downgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('nutrition_db_source')
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('nutrition_mode')
