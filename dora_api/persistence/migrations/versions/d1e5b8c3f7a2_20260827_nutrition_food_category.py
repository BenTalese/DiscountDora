"""20260827_nutrition_food_category

Health Star Rating (owner ask 2026-08-27) needs to know what fraction of a
recipe's weight is fruit, vegetables, nuts or legumes — the HSR "fvnl"
percentage, which is worth up to 8 modifying points and, above 13 baseline
points, is the gate that decides whether protein counts at all.

Nothing in Dora classified a food that way. It turns out USDA already does:
every FoodData Central bundle the importer downloads contains
`food_category.csv`, and `food.csv` carries a `food_category_id` — 100%
populated across all 7,793 SR Legacy foods, ~96% across the Foundation bundle.
The importer was reading neither. This column is where that description now
lands, verbatim.

Deliberately isolated (owner's call): nothing renders it, its only consumer is
`features/nutrition/food_categories.is_fvnl_category`, and it has no
relationship to `StockGroup` — the user's pantry filing system stays theirs.

**No backfill is possible here.** The category lives in the source dataset, not
in anything already stored, so existing rows keep NULL until the dataset is
re-imported. That is the honest outcome rather than a guess from the food's
name, and the admin nutrition page says so; a NULL category simply scores no
fvnl points, which the rating reports as coverage rather than hiding.

Revision ID: d1e5b8c3f7a2
Revises: c9f2a7d4e1b8
Create Date: 2026-08-27 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd1e5b8c3f7a2'
down_revision = 'c9f2a7d4e1b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('NutritionFood') as batch:
        batch.add_column(sa.Column('food_category', sa.String(128), nullable=True))

    # The admin switch for the feature the column exists to serve. Off
    # everywhere: HSR is an AU/NZ government scheme and an install elsewhere
    # should not be handed a national rating as if it were universal. Settings'
    # "Match this device" offers to turn it on when it detects an AU/NZ locale,
    # which is how the people it was designed for get it without hunting.
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'health_star_rating_enabled', sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ))


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('health_star_rating_enabled')
    with op.batch_alter_table('NutritionFood') as batch:
        batch.drop_column('food_category')
