"""20260816_nutrition_macros_plus

Owner call 2026-08-16 — "is that the only nutrition data we can pull?"

It was: energy + protein + carbs + fat. Four more nutrients now ride along —
sugars, saturated fat, fibre and sodium — the ones a shopper actually reads off
a pack, and the ones USDA and Open Food Facts both carry reliably. The long
vitamin/mineral tail was explicitly NOT taken: it needs a per-nutrient child
table and every source is sparse enough that the UI would be mostly blank.

All nullable, no backfill. Existing rows keep their energy/macros and report
the new columns as NULL until the dataset is re-imported — which is honest
(P12 No-invent: "this source didn't say" is not zero) and is what re-running
the importer under System → Nutrition fixes.

Sodium is stored in milligrams, matching how packs state it; everything else
is grams per 100g.

Revision ID: d3a7f2b91c60
Revises: c1d5e8b3f704
Create Date: 2026-08-16 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'd3a7f2b91c60'
down_revision = 'c1d5e8b3f704'
branch_labels = None
depends_on = None


_NEW_COLUMNS = (
    'sugars_g_per_100g',
    'saturated_fat_g_per_100g',
    'fibre_g_per_100g',
    'sodium_mg_per_100g',
)


def upgrade():
    with op.batch_alter_table('NutritionFood') as batch_op:
        for name in _NEW_COLUMNS:
            batch_op.add_column(sa.Column(name, sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('NutritionFood') as batch_op:
        for name in reversed(_NEW_COLUMNS):
            batch_op.drop_column(name)
