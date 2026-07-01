"""20260630_cook_event

Append-only log of "the user cooked this recipe today." Written by
POST /api/recipes/<id>/cook alongside the existing `available_meals`
bump on Recipe. Consumed by the Stock Item detail's History tab —
joined at projection time to the item's ingredient recipes so the
user sees "Used in Pasta Bake on 16 Jun".

FK to Recipe is `SET NULL` (not CASCADE) so deleting a recipe doesn't
wipe cook history; the denormalised `recipe_name` on each row keeps
the timeline entry legible. FK to User is also `SET NULL` for the
same reason.

Revision ID: c3d7f1a2b8e4
Revises: a4c8f2e1b9d3
Create Date: 2026-06-30 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'c3d7f1a2b8e4'
down_revision = 'a4c8f2e1b9d3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'CookEvent',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column(
            'recipe_id', UUIDType,
            sa.ForeignKey('Recipe.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('recipe_name', sa.String(length=255), nullable=False),
        sa.Column('meals_cooked', sa.Integer(), nullable=False),
        sa.Column(
            'cooked_by_user_id', UUIDType,
            sa.ForeignKey('User.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    )
    # The detail projection scans by recipe_id (bounded set of recipes
    # linked to the current stock item) and sorts by occurred_at.
    op.create_index(
        'cook_event_recipe_id',
        'CookEvent', ['recipe_id'],
    )


def downgrade():
    op.drop_index('cook_event_recipe_id', table_name='CookEvent')
    op.drop_table('CookEvent')
