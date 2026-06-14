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


def test_preview_empty_selection_is_empty():
    resp = requests.post(f"{MEAL_PLANS}/preview-ingredients", json={"recipes": []})
    assert resp.status_code == 200, resp.text
    assert resp.json() == []
