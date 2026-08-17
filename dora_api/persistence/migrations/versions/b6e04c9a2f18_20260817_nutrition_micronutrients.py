"""20260817_nutrition_micronutrients

Owner call 2026-08-17 — "what other nutrition data can be pulled? Possible to
have an optional section at the bottom for potassium, vitamin D, calcium,
iron, etc?"

Yes. This adds the vitamins-and-minerals block: the rest of the fat breakdown
(trans, mono-, polyunsaturated), cholesterol, five minerals and six vitamins.
Both sources carry all fifteen — USDA under the names in `nutrients.py`, Open
Food Facts under its `*_100g` nutriments keys.

This reverses the 2026-08-16 scope note ("the long vitamin/mineral tail needs a
per-nutrient child table"). That reasoning holds for the *full* USDA table —
hundreds of nutrients, individual fatty acids, amino-acid profiles — not for a
curated fifteen, which is a column apiece and no new join. The sparseness
concern is real and is answered in the UI instead: the block renders behind a
disclosure and is omitted entirely when a food knows none of it.

Units are in the column names, following `sodium_mg_per_100g`: milligrams for
the minerals a pack states in mg, micrograms for the vitamins it states in µg.
The OFF importer scales — OFF reports every non-energy nutriment in grams, so
these are ×1000 and ×1,000,000 conversions, and `nutrients.py` owns them.

All nullable, no backfill. Existing catalogue rows report the new columns as
NULL until the dataset is re-imported (P12 No-invent: "this source didn't say"
is not zero) — the same carve-out FU-645 tracks for the 2026-08-16 batch, and
the same fix: re-run the importer under Settings → Admin → Nutrition.

Revision ID: b6e04c9a2f18
Revises: a7f3c9d15e82
Create Date: 2026-08-17 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'b6e04c9a2f18'
down_revision = 'a7f3c9d15e82'
branch_labels = None
depends_on = None


# Order mirrors the GROUP_MORE entries in
# `dora_api/features/nutrition/nutrients.py`.
_NEW_COLUMNS = (
    'trans_fat_g_per_100g',
    'monounsaturated_fat_g_per_100g',
    'polyunsaturated_fat_g_per_100g',
    'cholesterol_mg_per_100g',
    'potassium_mg_per_100g',
    'calcium_mg_per_100g',
    'iron_mg_per_100g',
    'magnesium_mg_per_100g',
    'zinc_mg_per_100g',
    'vitamin_a_ug_per_100g',
    'vitamin_c_mg_per_100g',
    'vitamin_d_ug_per_100g',
    'vitamin_e_mg_per_100g',
    'vitamin_b12_ug_per_100g',
    'folate_ug_per_100g',
)


def upgrade():
    with op.batch_alter_table('NutritionFood') as batch_op:
        for name in _NEW_COLUMNS:
            batch_op.add_column(sa.Column(name, sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('NutritionFood') as batch_op:
        for name in reversed(_NEW_COLUMNS):
            batch_op.drop_column(name)
