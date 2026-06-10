"""20260609_recipe_tools

C-4 Chunk 5 — kitchen tools as a user-configurable vocabulary.

- New `Tool` lookup table ({id, name, sequence}), seeded with common defaults.
- New `RecipeTool` association (recipe_id, tool_id), CASCADE both ways.

Revision ID: b8e3f1a6d2c4
Revises: a7d2f4c9e1b8
Create Date: 2026-06-09 00:00:00.000000

"""
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'b8e3f1a6d2c4'
down_revision = 'a7d2f4c9e1b8'
branch_labels = None
depends_on = None


_DEFAULT_TOOLS = [
    "Frypan", "Saucepan", "Large pot", "Baking tray", "Oven dish",
    "Mixing bowl", "Food processor", "Blender", "Stand mixer",
    "Hand mixer", "Wok", "Slow cooker", "Air fryer", "Grater",
    "Whisk", "Colander", "Rolling pin", "Knife & board",
]


def upgrade():
    op.create_table(
        'Tool',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
    )
    tool_tbl = sa.table(
        'Tool',
        sa.column('id', UUIDType()),
        sa.column('name', sa.String),
        sa.column('sequence', sa.Integer),
    )
    op.bulk_insert(tool_tbl, [
        {'id': str(uuid.uuid4()), 'name': name, 'sequence': i}
        for i, name in enumerate(_DEFAULT_TOOLS)
    ])

    op.create_table(
        'RecipeTool',
        sa.Column(
            'recipe_id', UUIDType,
            sa.ForeignKey('Recipe.id', ondelete='CASCADE'),
            primary_key=True,
        ),
        sa.Column(
            'tool_id', UUIDType,
            sa.ForeignKey('Tool.id', ondelete='CASCADE'),
            primary_key=True,
        ),
    )
    op.create_index('ix_recipe_tool_tool_id', 'RecipeTool', ['tool_id'])


def downgrade():
    op.drop_index('ix_recipe_tool_tool_id', table_name='RecipeTool')
    op.drop_table('RecipeTool')
    op.drop_table('Tool')
