"""20260612_recipe_sections

C-4 Chunk 10 — multi-part recipes via named sections (DEC-3 option A).

- New `RecipeSection` table: `{id, recipe_id, sequence, name}`.
- `RecipeIngredient.section_id` (nullable FK → RecipeSection,
  ON DELETE SET NULL): rows with NULL section_id are the implicit "main"
  group, so existing recipes need no data migration.
- `RecipeStep.section_id` (nullable FK → RecipeSection,
  ON DELETE SET NULL): top-level steps may belong to a section; sub-steps
  inherit visually but the FK is stored per-row to keep reads flat.

Sub-recipes (DEC-3 option B) are explicitly deferred until real-world
signal that reuse matters.

Revision ID: f6c8e3a9b1d2
Revises: e5b9d2c8a4f3
Create Date: 2026-06-12 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'f6c8e3a9b1d2'
down_revision = 'e5b9d2c8a4f3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'RecipeSection',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column(
            'recipe_id', UUIDType,
            sa.ForeignKey('Recipe.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('name', sa.String(255), nullable=False),
    )
    op.create_index('ix_recipe_section_recipe_id', 'RecipeSection', ['recipe_id'])

    with op.batch_alter_table('RecipeIngredient') as batch_op:
        batch_op.add_column(sa.Column('section_id', UUIDType, nullable=True))
        batch_op.create_foreign_key(
            'fk_recipe_ingredient_section',
            'RecipeSection', ['section_id'], ['id'],
            ondelete='SET NULL',
        )

    with op.batch_alter_table('RecipeStep') as batch_op:
        batch_op.add_column(sa.Column('section_id', UUIDType, nullable=True))
        batch_op.create_foreign_key(
            'fk_recipe_step_section',
            'RecipeSection', ['section_id'], ['id'],
            ondelete='SET NULL',
        )


def downgrade():
    with op.batch_alter_table('RecipeStep') as batch_op:
        batch_op.drop_constraint('fk_recipe_step_section', type_='foreignkey')
        batch_op.drop_column('section_id')

    with op.batch_alter_table('RecipeIngredient') as batch_op:
        batch_op.drop_constraint('fk_recipe_ingredient_section', type_='foreignkey')
        batch_op.drop_column('section_id')

    op.drop_index('ix_recipe_section_recipe_id', table_name='RecipeSection')
    op.drop_table('RecipeSection')
