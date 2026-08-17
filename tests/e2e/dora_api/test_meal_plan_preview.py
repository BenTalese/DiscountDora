"""Meal Plans C-2.J — preview ingredients for an unsaved selection."""
import requests

MEAL_PLANS = "http://localhost:5170/api/meal-plans"
RECIPES = "http://localhost:5170/api/recipes"


def _recipe_with_ingredients() -> str | None:
    items = requests.get(f"{RECIPES}?limit=50").json()["items"]
    return next((r["recipe_id"] for r in items if r.get("ingredients")), None)


def test_preview_ingredients_returns_aggregated_list():
    resp = requests.post(f"{MEAL_PLANS}/preview-ingredients", json={
        "recipes": [{"recipe_id": _recipe_with_ingredients() or requests.get(f"{RECIPES}?limit=1").json()["items"][0]["recipe_id"], "servings": 2}],
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    for ing in body:
        assert "stock_item_id" in ing
        assert "used_in_recipe_ids" in ing


def _recipe_with_unlinked_ingredient() -> str | None:
    """A paste-imported recipe carrying at least one ingredient that was never
    linked to a stock item (Chunk 4). The dev seed ships two."""
    items = requests.get(f"{RECIPES}?limit=50").json()["items"]
    return next(
        (r["recipe_id"] for r in items if r.get("unlinked_ingredient_count", 0) > 0),
        None,
    )


def test_preview_ingredients_with_unlinked_ingredient_does_not_500():
    """Regression: the aggregator read `.id` off a None stock item, so ONE
    unlinked row anywhere in the selection 500'd the endpoint (and the saved
    plan's /ingredients with it). Unlinked rows are skipped — a shopping list
    is a list of stock items, and an unlinked row isn't one yet."""
    recipe_id = _recipe_with_unlinked_ingredient()
    if recipe_id is None:
        import pytest
        pytest.skip("no seeded recipe with an unlinked ingredient")
    resp = requests.post(f"{MEAL_PLANS}/preview-ingredients", json={
        "recipes": [{"recipe_id": recipe_id, "servings": 2}],
    })
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)


def test_preview_empty_selection_is_empty():
    resp = requests.post(f"{MEAL_PLANS}/preview-ingredients", json={"recipes": []})
    assert resp.status_code == 200, resp.text
    assert resp.json() == []
