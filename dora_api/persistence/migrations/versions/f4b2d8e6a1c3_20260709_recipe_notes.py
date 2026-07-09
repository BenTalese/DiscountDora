"""20260709_recipe_notes

RD-29 (FU-432) — free-text personal notes on a recipe. Adds `Recipe.notes`
(Text, nullable). Distinct from `instructions` (the method); this is the
cook's own commentary, surfaced in cook mode under the steps. Nullable, no
backfill — existing recipes simply have no note.

Revision ID: f4b2d8e6a1c3
Revises: e3a9c7b1f2d8
Create Date: 2026-07-09 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'f4b2d8e6a1c3'
down_revision = 'e3a9c7b1f2d8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Recipe') as batch:
        batch.add_column(sa.Column('notes', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('Recipe') as batch:
        batch.drop_column('notes')
