"""FU — `POST /onboarding/seed-demo` on a genuinely fresh install.

The demo seed has two paths and only one of them was ever exercised here: on a
dev-seeded (or already-onboarded) DB the "Spaghetti Aglio e Olio" recipe
already exists, so the handler short-circuits on its idempotency check and the
row-creating half never runs. A real first-run install has neither the recipe
nor its three pantry items, and that half went stale — it was still passing an
`image=` kwarg to `StockItem`, a field the entity dropped, so every genuine
first setup that ticked "Add a demo recipe + this-week meal plan" 500'd and the
wizard's Finish could not complete.

This test forces the fresh-install branch: drop the recipes, and rename the
demo's ingredients out of the way so the handler has to create its own.
"""
import requests
from sqlalchemy import text

from dora_api.app import app, db

BASE = "http://localhost:5170/api"
SEED_DEMO = f"{BASE}/onboarding/seed-demo"

_DEMO_INGREDIENT_NAMES = ("Spaghetti pasta", "Garlic cloves", "Olive oil")


def _force_fresh_install_state() -> None:
    """No recipes, and none of the demo's ingredients present by name."""
    with app.app_context():
        with db.engine.begin() as conn:
            conn.execute(text('DELETE FROM "MealPlanEntry"'))
            conn.execute(text('DELETE FROM "RecipeIngredient"'))
            conn.execute(text('DELETE FROM "Recipe"'))
            for name in _DEMO_INGREDIENT_NAMES:
                # Match the handler's own case-insensitive, trimmed lookup —
                # an exact-name UPDATE leaves near-miss rows behind and the
                # handler then reuses one instead of creating it.
                conn.execute(
                    text(
                        'UPDATE "StockItem" SET name = :new '
                        "WHERE lower(trim(name)) = :old"
                    ),
                    {"new": f"zz-renamed {name}", "old": name.strip().lower()},
                )
        db.session.remove()


def test__seed_demo__fresh_install__creates_items_recipe_and_plan(api):
    _force_fresh_install_state()

    response = requests.post(SEED_DEMO)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["seeded"] is True, body
    # The row-creating half actually ran: all three ingredients were missing,
    # so the handler had to construct StockItems itself (the branch that broke).
    assert body["items_created"] == len(_DEMO_INGREDIENT_NAMES), body
    assert body["recipe_created"] is True, body
    assert body["meal_plan_created"] is True, body


def test__seed_demo__second_call__is_a_no_op(api):
    _force_fresh_install_state()
    assert requests.post(SEED_DEMO).json()["seeded"] is True

    repeat = requests.post(SEED_DEMO)

    assert repeat.status_code == 200, repeat.text
    assert repeat.json() == {
        "seeded": False,
        "items_created": 0,
        "recipe_created": False,
        "meal_plan_created": False,
    }
