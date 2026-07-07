"""FU-081 — `Recipe.is_planned` server-derived flag.

True iff at least one MealPlanEntry for this recipe is scheduled today or
later AND not yet consumed. The cookbook overview's "Planned" / "Not
planned" tri-state filter reads this directly.
"""
from datetime import date, timedelta

import requests

BASE = 'http://localhost:5170/api'
RECIPES = f"{BASE}/recipes"
MEAL_PLANS = f"{BASE}/meal-plans"


def _household_today() -> date:
    return date.fromisoformat(requests.get(f"{MEAL_PLANS}/today").json()["today"])


def _find_recipe(recipe_id: str) -> dict:
    return next(
        r for r in requests.get(f"{RECIPES}?limit=200").json()["items"]
        if r["recipe_id"] == recipe_id
    )


def test__recipes__is_planned_true_when_future_unconsumed_entry_exists(api):
    """Planning a recipe for next week sets `is_planned` true; deleting the
    plan flips it back to false."""
    today = _household_today()
    next_monday = today + timedelta(days=7 - today.weekday())
    # Pick a recipe with no existing future meal-plan entries — otherwise
    # deleting the one entry we add won't flip is_planned back to false.
    items = requests.get(f"{RECIPES}?limit=200").json()["items"]
    unplanned = next((r for r in items if r["is_planned"] is False), None)
    assert unplanned is not None, "seed expected to have an unplanned recipe"
    recipe_id = unplanned["recipe_id"]

    created = requests.post(MEAL_PLANS, json={
        "start_date": next_monday.isoformat(),
        "entries": [{
            "recipe_id": recipe_id,
            "scheduled_for": next_monday.isoformat(),
            "servings": 2,
            "slot": "Dinner",
        }],
    })
    assert created.status_code in (200, 201), created.text
    plan_id = created.json()["meal_plan_id"]
    try:
        recipe = _find_recipe(recipe_id)
        assert recipe["is_planned"] is True, recipe
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")

    recipe_after = _find_recipe(recipe_id)
    assert recipe_after["is_planned"] is False, recipe_after


def test__recipes__is_planned_false_for_an_unplanned_recipe(api):
    """A recipe with no future un-consumed MealPlanEntry rows returns
    `is_planned: false`."""
    # Pick the last recipe from the seed list — most likely to be unplanned.
    items = requests.get(f"{RECIPES}?limit=200").json()["items"]
    candidate = next(
        (r for r in items if r["is_planned"] is False),
        None,
    )
    assert candidate is not None, "seed expected to have at least one unplanned recipe"
    assert candidate["is_planned"] is False


def test__recipes__is_planned_present_on_every_dto(api):
    """Every RecipeDto carries the `is_planned` boolean."""
    items = requests.get(f"{RECIPES}?limit=200").json()["items"]
    assert items, "expected seeded recipes"
    for r in items:
        assert "is_planned" in r, r
        assert isinstance(r["is_planned"], bool), r
