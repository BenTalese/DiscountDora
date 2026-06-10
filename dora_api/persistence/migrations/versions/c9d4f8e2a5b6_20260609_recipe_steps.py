"""20260609_recipe_steps

C-4 Chunk 6 — structured recipe steps.

- New `RecipeStep` table — one row per step (or sub-step). Self-referential
  `parent_step_id` gives exactly one level of sub-steps (top-level steps
  have NULL; sub-steps point at their parent). `sequence` is the order
  within the parent (or among top-level steps when parent is NULL).
- `RecipeStepIngredient` (step_id, recipe_ingredient_id) — which of the
  recipe's own ingredients this step uses.
- `RecipeStepTool` (step_id, recipe_tool) — depends on the Chunk 5 Tool
  vocab. Stored as (step_id, tool_id); ON DELETE CASCADE both ways.

Existing recipes' `instructions` text stays as-is. A recipe with no
`RecipeStep` rows is "unstructured" and the cook-mode fallback path
keeps splitting `instructions` by newline.

Revision ID: c9d4f8e2a5b6
Revises: b8e3f1a6d2c4
Create Date: 2026-06-09 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'c9d4f8e2a5b6'
down_revision = 'b8e3f1a6d2c4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'RecipeStep',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column(
            'recipe_id', UUIDType,
            sa.ForeignKey('Recipe.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'parent_step_id', UUIDType,
            sa.ForeignKey('RecipeStep.id', ondelete='CASCADE'),
            nullable=True,
        ),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('hint', sa.Text(), nullable=True),
    )
    op.create_index('ix_recipe_step_recipe_id', 'RecipeStep', ['recipe_id'])
    op.create_index('ix_recipe_step_parent_id', 'RecipeStep', ['parent_step_id'])

    op.create_table(
        'RecipeStepIngredient',
        sa.Column(
            'step_id', UUIDType,
            sa.ForeignKey('RecipeStep.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column(
            'recipe_ingredient_id', UUIDType,
            sa.ForeignKey('RecipeIngredient.id', ondelete='CASCADE'),
            primary_key=True,
        ),
    )
    op.create_index(
        'ix_recipe_step_ingredient_ingredient_id',
        'RecipeStepIngredient', ['recipe_ingredient_id'],
    )

    op.create_table(
        'RecipeStepTool',
        sa.Column(
            'step_id', UUIDType,
            sa.ForeignKey('RecipeStep.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column(
            'tool_id', UUIDType,
            sa.ForeignKey('Tool.id', ondelete='CASCADE'),
            primary_key=True,
        ),
    )
    op.create_index(
        'ix_recipe_step_tool_tool_id', 'RecipeStepTool', ['tool_id'],
    )


def downgrade():
    op.drop_index('ix_recipe_step_tool_tool_id', table_name='RecipeStepTool')
    op.drop_table('RecipeStepTool')
    op.drop_index(
        'ix_recipe_step_ingredient_ingredient_id',
        table_name='RecipeStepIngredient',
    )
    op.drop_table('RecipeStepIngredient')
    op.drop_index('ix_recipe_step_parent_id', table_name='RecipeStep')
    op.drop_index('ix_recipe_step_recipe_id', table_name='RecipeStep')
    op.drop_table('RecipeStep')
