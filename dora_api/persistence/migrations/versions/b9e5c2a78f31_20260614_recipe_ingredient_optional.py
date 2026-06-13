"""20260614_recipe_ingredient_optional

Cookbook card revision §1.9 — optional ingredients. New
`RecipeIngredient.is_optional` boolean column, NOT NULL with server
default `0`, so existing rows stay valid through the upgrade. The
cookability rule continues to ignore this flag (no
`cookable_with_optional` half-state); the column simply lets the
edit dialog mark a row, the picker render it under an Optional
separator, and cook mode dim it.

Batch mode so the add works on SQLite (table rebuild) as well as
Postgres — R-005 portable data access.

Revision ID: b9e5c2a78f31
Revises: a1c4e7b3f5d2
Create Date: 2026-06-14 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'b9e5c2a78f31'
down_revision = 'a1c4e7b3f5d2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('RecipeIngredient') as batch:
        batch.add_column(
            sa.Column(
                'is_optional',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('0'),
            ),
        )


def downgrade():
    with op.batch_alter_table('RecipeIngredient') as batch:
        batch.drop_column('is_optional')
