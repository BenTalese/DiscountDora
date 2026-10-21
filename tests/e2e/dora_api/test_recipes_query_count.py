"""FU-138 — GET /api/recipes must not regress into N+1 query patterns.

The list handler batches every per-recipe lookup (cookability,
ingredients, dietary tags, tools, sections, sibling/plan rollups,
expiring-ingredient counts, image-flag, …). This test pins that
shape: doubling the recipe count must not double the SELECT count.

Approach is a ratio test rather than a hard ceiling — pinning a
precise number would be brittle as new batched lookups get added.
Adding N recipes is allowed to add a small constant number of
SELECTs (a few extra IN-list shards), but must not add ≈N.
"""
import requests

from tests.e2e.dora_api._query_counter import SelectCounter
from tests.support import set_money_enabled


BASE = "http://localhost:5170/api"
RECIPES = f"{BASE}/recipes"

# Big enough that an honest N+1 (one extra SELECT per recipe) is loud
# above the per-call constant overhead; small enough that the test
# stays well under a second.
EXTRA_RECIPES = 10

# Per-recipe ceiling for the (loaded - baseline) SELECT delta. An N+1
# regression would push this to ≥1.0 per recipe; the current handler
# sits at ~0. Set generously so a benign batched-query shift (e.g.
# adding one more shared IN-load) doesn't flake the test.
PER_RECIPE_BUDGET = 0.5


def _count_list_selects() -> tuple[int, int]:
    """Return (select_count, items_returned) for one GET /recipes hit."""
    with SelectCounter() as qc:
        response = requests.get(f"{RECIPES}?limit=500")
        assert response.status_code == 200, response.text
        items = response.json()["items"]
    return qc.count, len(items)


def test__get_recipes__select_count_does_not_scale_with_recipe_count(api):
    """Adding 10 recipes must not add ~10 SELECTs to the list handler.

    If this fails, something on the recipe-list hot path went from a
    batched lookup to a per-recipe one. Likely culprits live in
    `dora_api/features/recipes/get_recipes.py` — check any new
    `for recipe in …: repository.get(…)` loop.
    """
    baseline_selects, baseline_items = _count_list_selects()

    created_ids: list[str] = []
    try:
        for i in range(EXTRA_RECIPES):
            response = requests.post(RECIPES, json={
                "name": f"_fu138_probe_{i}",
                "ingredients": [],
            })
            assert response.status_code in (200, 201), response.text
            created_ids.append(response.json()["recipe_id"])

        loaded_selects, loaded_items = _count_list_selects()
        assert loaded_items == baseline_items + EXTRA_RECIPES, (
            f"setup error: expected {baseline_items + EXTRA_RECIPES} "
            f"recipes after probe inserts, got {loaded_items}"
        )

        delta = loaded_selects - baseline_selects
        budget = EXTRA_RECIPES * PER_RECIPE_BUDGET
        assert delta < budget, (
            f"GET /recipes looks N+1: adding {EXTRA_RECIPES} recipes "
            f"grew the SELECT count by {delta} (baseline "
            f"{baseline_selects} → {loaded_selects}). Per-recipe budget "
            f"is {PER_RECIPE_BUDGET} → total budget {budget}. Inspect "
            f"recent changes to dora_api/features/recipes/get_recipes.py "
            f"for a new per-recipe lookup."
        )
    finally:
        for recipe_id in created_ids:
            requests.delete(f"{RECIPES}/{recipe_id}")


def test__get_recipes__cost_hydration_does_not_scale_with_recipe_count(api):
    """Same guard, with money ON — the cost hydrator only runs then.

    Owner 2026-09-05 put `estimated_cost` on the cookbook list, where it had
    deliberately never been: the per-recipe pricing path is two queries, so
    costing a 50-card page one recipe at a time is a 100-query page. The list
    goes through `recipe_cost.estimate_costs_for`, which is two queries for the
    *whole* page regardless of size.

    The test above cannot catch a regression here, because `money_enabled`
    server-defaults to False and the hydrator returns early — so without this
    case the entire new code path is unguarded. If someone swaps the batch call
    for a loop over `estimate_cost_for_ingredients`, this is what fails.
    """
    original = requests.get(f"{BASE}/app-settings").json()["money_enabled"]
    set_money_enabled(True)

    created_ids: list[str] = []
    try:
        baseline_selects, baseline_items = _count_list_selects()

        for i in range(EXTRA_RECIPES):
            response = requests.post(RECIPES, json={
                "name": f"_cost_probe_{i}",
                "ingredients": [],
            })
            assert response.status_code in (200, 201), response.text
            created_ids.append(response.json()["recipe_id"])

        loaded_selects, _ = _count_list_selects()

        delta = loaded_selects - baseline_selects
        budget = EXTRA_RECIPES * PER_RECIPE_BUDGET
        assert delta < budget, (
            f"GET /recipes looks N+1 with money on: adding {EXTRA_RECIPES} "
            f"recipes grew the SELECT count by {delta} (baseline "
            f"{baseline_selects} → {loaded_selects}, budget {budget}). "
            f"Check `_hydrate_estimated_cost` in "
            f"dora_api/features/recipes/get_recipes.py — it must call "
            f"`estimate_costs_for` once for the page, not once per recipe."
        )
    finally:
        for recipe_id in created_ids:
            requests.delete(f"{RECIPES}/{recipe_id}")
        set_money_enabled(original)
