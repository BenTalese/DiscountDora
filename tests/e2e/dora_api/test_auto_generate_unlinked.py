"""FU-505 — the auto-generator's `unlinked_skipped` warning payload.

When "Generate shopping list for this week" (or a recipe source) pulls a recipe
whose ingredient has **no linked StockItem**, there's no stock-item id to anchor
a shopping-list line, so the ingredient can't be added. Rather than drop it
silently, `POST /api/shopping-lists/auto-generate` returns it in
`unlinked_skipped` (`{recipe_name, ingredient_name}`) so the SPA can show the
"Add these manually" dialog. Linked ingredients still become lines as normal.

The provenance-priority merge + the zero-candidate defer are pinned elsewhere
(test_auto_generate_priority.py / test_auto_generate_draft_shop.py); this file
pins the unlinked-warning contract, which had no coverage.

Per-test DB rollback (conftest) restores the seed after each test, so the
shopping lists these create don't leak.
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
AUTO_GENERATE = f"{BASE}/shopping-lists/auto-generate"
RECIPES = f"{BASE}/recipes"
STOCK_ITEMS = f"{BASE}/stock-items"
STOCK_LEVELS = f"{BASE}/stock-levels"


def _level_id(name: str) -> str:
    levels = requests.get(STOCK_LEVELS).json()["items"]
    return next(l["stock_level_id"] for l in levels if l["name"] == name)


def _create_out_of_stock_item(name: str) -> str:
    # Out of Stock so the linked ingredient is a genuine candidate line (the
    # collector subtracts only Stocked items).
    resp = requests.post(STOCK_ITEMS, json={
        "name": name,
        "stock_level_id": _level_id("Out of Stock"),
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["stock_item_id"]


def _create_recipe(name: str, ingredients: list[dict]) -> str:
    resp = requests.post(RECIPES, json={"name": name, "ingredients": ingredients})
    assert resp.status_code == 201, resp.text
    return resp.json()["recipe_id"]


def _generate_from_recipe(recipe_id: str) -> dict:
    resp = requests.post(AUTO_GENERATE, json={"sources": {"recipes": [recipe_id]}})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test__auto_generate__recipe_with_unlinked_ingredient__surfaces_it(api):
    linked_item = _create_out_of_stock_item(f"linked-{uuid4()}")
    recipe_name = f"unlinked-recipe-{uuid4()}"
    recipe_id = _create_recipe(recipe_name, [
        {"stock_item_id": linked_item},          # anchored → becomes a line
        {"raw_text": "a pinch of saffron"},      # no stock item → unlinked
    ])

    body = _generate_from_recipe(recipe_id)

    # The unlinked ingredient is reported, tagged with its recipe.
    assert body["unlinked_skipped"] == [
        {"recipe_name": recipe_name, "ingredient_name": "a pinch of saffron"},
    ]
    # ...and the linked out-of-stock ingredient still became a line.
    line_item_ids = {l["stock_item_id"] for l in body["lines"]}
    assert linked_item in line_item_ids
    assert body["added_count"] >= 1


def test__auto_generate__fully_linked_recipe__no_unlinked_warning(api):
    linked_item = _create_out_of_stock_item(f"linked-only-{uuid4()}")
    recipe_id = _create_recipe(f"fully-linked-{uuid4()}", [
        {"stock_item_id": linked_item},
    ])

    body = _generate_from_recipe(recipe_id)

    assert body["unlinked_skipped"] == []
    assert linked_item in {l["stock_item_id"] for l in body["lines"]}


def test__auto_generate__multiple_unlinked__reported_per_recipe(api):
    # Two unlinked ingredients on one recipe → both reported, both tagged with
    # the same recipe name; order follows the recipe's ingredient order.
    recipe_name = f"multi-unlinked-{uuid4()}"
    recipe_id = _create_recipe(recipe_name, [
        {"raw_text": "fresh basil"},
        {"raw_text": "sea salt"},
    ])

    body = _generate_from_recipe(recipe_id)

    names = [u["ingredient_name"] for u in body["unlinked_skipped"]]
    assert names == ["fresh basil", "sea salt"]
    assert all(u["recipe_name"] == recipe_name for u in body["unlinked_skipped"])
    # No linked items → nothing to add as lines.
    assert body["added_count"] == 0
