"""20260610_recipe_versions

C-4 Chunk 8 — version sibling grouping (per DEC-2).

Recipes that share a `version_group_id` are versions of each other (no
current pointer, no snapshot/current distinction — they're equal peers).
NULL means the recipe is a singleton; it'll absorb future versions when
the user creates one.

The detail endpoint asks "who else shares this group id?" on every
recipe load, so the column is indexed.

Revision ID: e1f6a2b4c8d9
Revises: d0e5f1a3b8c7
Create Date: 2026-06-10 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'e1f6a2b4c8d9'
down_revision = 'd0e5f1a3b8c7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Recipe') as batch_op:
        batch_op.add_column(sa.Column('version_group_id', UUIDType, nullable=True))
        batch_op.create_index('ix_recipe_version_group_id', ['version_group_id'])


def downgrade():
    with op.batch_alter_table('Recipe') as batch_op:
        batch_op.drop_index('ix_recipe_version_group_id')
        batch_op.drop_column('version_group_id')
