"""20260820_recipe_categories_no_time_of_day

Owner feedback 2026-08-20 (cookbook batch 3): *"Noticed on my dev data time of
day options mixed in with category. Lets make sure there's no time of day e.g.
'dinner' in the prod seed data or onboarding pickable start packs."*

The default **Category** vocabulary shipped three names that are also **MealSlot**
(time-of-day) names — ``Breakfast``, ``Dessert``, ``Snack``. Two independent
facets offering the same words is what made the cookbook's Category dropdown
read as a time-of-day picker, and it let one recipe carry the same value twice
(``category="Dessert"`` *and* ``time_of_day="Dessert"`` — the dev seed did
exactly that).

Category is now strictly a **dish type**. The three overlapping names are
deleted and three dish types take their place (``Curry``, ``Bake``, ``Bread``),
per the owner's pick, so the list still covers the common shapes at the same
length as before.

* **Recipes pointing at a deleted category keep everything else.** The FK is
  ``ondelete='SET NULL'``, but SQLite does not enforce FKs unless the pragma is
  on, so the NULLing is done explicitly first rather than trusted to the engine.
  The information is not lost: a recipe that *was* a "Dessert" category almost
  certainly also carries ``time_of_day='Dessert'``, which is where that fact
  belongs and which this migration does not touch.
* **Insert is by-name conditional and the whole set is resequenced**, so this is
  idempotent and also repairs an install where someone had already renamed or
  re-ordered part of the list by hand.
* Starter packs were checked and are clean — they seed *stock items* from
  ``starter_packs.json``, never recipe categories.

``downgrade`` restores the three time-of-day names and drops the three dish
types, symmetrically. Recipes NULLed on the way up are not re-pointed — the
mapping is gone by then, and NULL is the honest value.

Revision ID: c8b3e5f0a712
Revises: f2a6d4b8c917
Create Date: 2026-08-20 00:00:00.000000
"""
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'c8b3e5f0a712'
down_revision = 'f2a6d4b8c917'
branch_labels = None
depends_on = None

# Names that collide with the MealSlot vocabulary (see MEAL_SLOT_NAMES in
# `seed_builders.py` — Breakfast / Lunch / Dinner / Snack / Dessert). Lunch and
# Dinner were never category defaults, hence three and not five.
_TIME_OF_DAY_NAMES = ['Breakfast', 'Dessert', 'Snack']
_NEW_DISH_TYPES = ['Curry', 'Bake', 'Bread']

# The canonical ordering after this migration. Mirrors CATEGORY_NAMES in
# `dora_api/persistence/seed_builders.py` — the two must stay in step so a
# create_all dev/test DB and a migrated prod DB show the same list in the same
# order.
_CATEGORIES_AFTER = [
    "Main", "Pasta", "Rice", "Stir fry", "Curry", "Soup", "Salad", "Side",
    "Bake", "Bread", "Drink", "Sauce",
]
_CATEGORIES_BEFORE = [
    "Main", "Pasta", "Rice", "Stir fry", "Soup", "Salad", "Side",
    "Breakfast", "Dessert", "Snack", "Drink", "Sauce",
]

_category_tbl = sa.table(
    'Category',
    sa.column('id', UUIDType()),
    sa.column('name', sa.String),
    sa.column('sequence', sa.Integer),
)


def _swap(drop_names, add_names, final_order):
    conn = op.get_bind()

    doomed = conn.execute(
        sa.text(
            'SELECT id FROM "Category" WHERE name IN :names'
        ).bindparams(sa.bindparam('names', expanding=True)),
        {'names': drop_names},
    ).scalars().all()
    if doomed:
        conn.execute(
            sa.text(
                'UPDATE "Recipe" SET category_id = NULL '
                'WHERE category_id IN :ids'
            ).bindparams(sa.bindparam('ids', expanding=True)),
            {'ids': doomed},
        )
        conn.execute(
            sa.text(
                'DELETE FROM "Category" WHERE id IN :ids'
            ).bindparams(sa.bindparam('ids', expanding=True)),
            {'ids': doomed},
        )

    existing = set(
        conn.execute(sa.text('SELECT name FROM "Category"')).scalars().all()
    )
    missing = [n for n in add_names if n not in existing]
    if missing:
        op.bulk_insert(_category_tbl, [
            {'id': str(uuid.uuid4()), 'name': name, 'sequence': 0}
            for name in missing
        ])

    # Resequence the canonical names to the intended order; anything the user
    # added themselves keeps its own sequence and sorts after them.
    for i, name in enumerate(final_order):
        conn.execute(
            sa.text('UPDATE "Category" SET sequence = :seq WHERE name = :name'),
            {'seq': i, 'name': name},
        )


def upgrade():
    _swap(_TIME_OF_DAY_NAMES, _NEW_DISH_TYPES, _CATEGORIES_AFTER)


def downgrade():
    _swap(_NEW_DISH_TYPES, _TIME_OF_DAY_NAMES, _CATEGORIES_BEFORE)
