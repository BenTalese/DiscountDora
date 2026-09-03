"""GET /api/stock-items/planned-demand — the HTTP seam (owner, 2026-09-03).

The rules are unit-pinned in `tests/test_planned_demand.py`. What only a live
request can prove is the part that has broken repeatedly in this codebase:
**the relationship reads**. `MealPlanEntry.recipe` and
`RecipeIngredient.stock_item` are both `lazy="noload"`, so the naive walk
returns `None` silently and the endpoint answers "nothing planned" for a fully
planned week — the same failure shape as the buy-verdict bug (R-032). A unit
test over pure functions cannot see that; a request that plans three meals and
expects three back can.

Determinism: dates derive from the household-today anchor and slots from the
live vocabulary, per the 2026-07-10 timezone-flake rule.
"""
from datetime import timedelta
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
DEMAND = f"{BASE}/stock-items/planned-demand"
MEAL_PLANS = f"{BASE}/meal-plans"
RECIPES = f"{BASE}/recipes"


def _household_today():
    from datetime import date
    return date.fromisoformat(requests.get(f"{MEAL_PLANS}/today").json()["today"])


def _slot() -> str:
    return requests.get(f"{BASE}/meal-slots").json()[0]["name"]


def _stock_level_id(sequence: int) -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == sequence)


def _make_item(sequence: int) -> str:
    resp = requests.post(f"{BASE}/stock-items", json={
        "name": f"demand-{uuid4().hex[:8]}",
        "stock_level_id": _stock_level_id(sequence),
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["stock_item_id"]


def _make_recipe(stock_item_id: str, *, optional: bool = False) -> str:
    resp = requests.post(RECIPES, json={
        "name": f"Demand Recipe {uuid4().hex[:8]}",
        "servings": 2,
        "ingredients": [{
            "stock_item_id": stock_item_id,
            "quantity": 1,
            "unit": "cup",
            "client_id": "i1",
            "is_optional": optional,
        }],
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["recipe_id"]


def _plan(recipe_id: str, day_offsets, servings: int = 2) -> str:
    today = _household_today()
    slot = _slot()
    resp = requests.post(MEAL_PLANS, json={
        "start_date": today.isoformat(),
        "entries": [
            {"recipe_id": recipe_id,
             "scheduled_for": (today + timedelta(days=d)).isoformat(),
             "servings": servings, "slot": slot}
            for d in day_offsets
        ],
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["meal_plan_id"]


def _demand_for(item_id: str) -> dict | None:
    body = requests.get(DEMAND).json()
    assert body["enabled"] is True, body
    return body["demand"].get(item_id)


# ── the relationship reads actually resolve ──────────────────────────────

def test__planned_demand__counts_every_upcoming_meal_that_needs_the_item(api):
    item = _make_item(2)  # Out
    recipe = _make_recipe(item)
    _plan(recipe, [1, 3, 5])

    row = _demand_for(item)
    assert row is not None, "a planned recipe's required ingredient must appear"
    assert row["planned_meals"] == 3
    assert row["covered_meals"] == 0
    assert row["needed_meals"] == 3
    # Out + demand is the hard case, and it outranks Low (owner's grading).
    assert row["urgency"] == "blocking"
    assert row["earliest_needed"] == (_household_today() + timedelta(days=1)).isoformat()
    assert "3 planned meals" in row["reason"]


def test__planned_demand__low_item_is_a_watch_not_a_blocker(api):
    item = _make_item(1)  # Low
    _plan(_make_recipe(item), [2])
    assert _demand_for(item)["urgency"] == "watch"


def test__planned_demand__stocked_item_is_reported_but_not_urgent(api):
    # The count is still a fact worth having (the shopping surfaces can use
    # it); it just isn't a nudge while the cupboard says you're fine.
    item = _make_item(0)  # Stocked
    _plan(_make_recipe(item), [2])
    row = _demand_for(item)
    assert row["planned_meals"] == 1 and row["urgency"] == "none"


def test__planned_demand__cooked_batch_pool_covers_the_soonest_meals(api):
    item = _make_item(2)
    recipe = _make_recipe(item)
    _plan(recipe, [1, 3, 5], servings=2)
    # Four servings already cooked: the first two meals are covered, the third
    # is not — the owner's "2 have been allocated a meal" reading.
    bumped = requests.post(f"{RECIPES}/{recipe}/adjust-meals", json={"delta": 4})
    assert bumped.status_code == 200, bumped.text

    row = _demand_for(item)
    assert row["planned_meals"] == 3
    assert row["covered_meals"] == 2
    assert row["needed_meals"] == 1
    assert row["earliest_needed"] == (_household_today() + timedelta(days=5)).isoformat()
    assert "2 already covered by a cooked batch" in row["reason"]


def test__planned_demand__optional_ingredients_are_not_demand(api):
    item = _make_item(2)
    _plan(_make_recipe(item, optional=True), [1, 2])
    assert _demand_for(item) is None
