"""FU-635 chunk 6 — recipe nutrition rollup over the real request path.

The arithmetic is pinned in `tests/test_nutrition_recipe_rollup.py` with the
repository stubbed. What only a real request proves is the wiring: that the
detail endpoint gathers foods + portions through the repository (the mapping
carries no relationship object, so a missed join fails silently as "nothing
convertible"), that the mode gate actually suppresses the field outside
complex, and that the list endpoint stays cheap.
"""
from datetime import datetime, timezone
from uuid import uuid4

import requests

from dora_api.app import app
from dora_api.domain.entities.nutrition_food import (
    NUTRITION_SOURCE_USDA_SR_LEGACY, NutritionFood,
)
from dora_api.domain.entities.nutrition_portion import NutritionPortion
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"
RECIPES = f"{BASE}/recipes"
APP_SETTINGS = f"{BASE}/app-settings"


def _set_mode(mode: str) -> None:
    resp = requests.patch(APP_SETTINGS, json={"nutrition_mode": mode})
    assert resp.status_code in (200, 204), resp.text


def _seed_foods() -> dict:
    """Flour (mass-only) and a banana that carries a whole-item portion."""
    with app.app_context():
        repo = SqlAlchemyRepository()
        now = datetime.now(timezone.utc)
        flour = NutritionFood(
            id=uuid4(), source=NUTRITION_SOURCE_USDA_SR_LEGACY,
            source_ref=f"f-{uuid4().hex[:8]}", name="Flour, wheat, all-purpose",
            kcal_per_100g=364.0, protein_g_per_100g=10.3, carbs_g_per_100g=76.3,
            fat_g_per_100g=1.0, imported_at=now,
        )
        banana = NutritionFood(
            id=uuid4(), source=NUTRITION_SOURCE_USDA_SR_LEGACY,
            source_ref=f"b-{uuid4().hex[:8]}", name="Bananas, raw",
            kcal_per_100g=89.0, protein_g_per_100g=1.09, imported_at=now,
        )
        repo.add(flour)
        repo.add(banana)
        repo.add(NutritionPortion(
            id=uuid4(), nutrition_food_id=banana.id,
            amount=1, measure="medium", gram_weight=100.0,
        ))
        repo.save_changes()
        return {"flour": str(flour.id), "banana": str(banana.id)}


def _linked_item(name: str, food_id: str | None) -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    item_id = make_stock_item(
        stock_level_id=levels[0]["stock_level_id"],
        name=f"{name} {uuid4().hex[:6]}",
    )["stock_item_id"]
    if food_id is not None:
        resp = requests.patch(f"{BASE}/stock-items/{item_id}", json={
            "nutrition_food_id": food_id,
        })
        assert resp.status_code in (200, 204), resp.text
    return item_id


def _make_recipe(ingredients: list, servings: int | None = None) -> str:
    body = {"name": f"rollup-probe-{uuid4()}", "ingredients": ingredients}
    if servings is not None:
        body["servings"] = servings
    resp = requests.post(RECIPES, json=body)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["recipe_id"]


def _detail(recipe_id: str) -> dict:
    resp = requests.get(f"{RECIPES}/{recipe_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


def test__recipe_detail__ComplexMode__RollsUpPerServingWithCoverage(api):
    foods = _seed_foods()
    _set_mode("complex")
    try:
        recipe_id = _make_recipe(
            [
                {"stock_item_id": _linked_item("Flour", foods["flour"]),
                 "quantity": 400, "unit": "g"},
                # Whole-item portion: 2 × 100g of banana.
                {"stock_item_id": _linked_item("Banana", foods["banana"]),
                 "quantity": 2, "unit": None},
                # Linked to no food at all — a named gap, not a silent one.
                {"stock_item_id": _linked_item("Salt", None),
                 "quantity": 5, "unit": "g"},
            ],
            servings=4,
        )

        nutrition = _detail(recipe_id)["nutrition"]

        assert nutrition["basis"] == "serving"
        assert nutrition["servings"] == 4
        # (400g flour @364 + 200g banana @89) / 4 servings.
        assert nutrition["kcal"] == round((4 * 364 + 2 * 89) / 4)
        assert nutrition["counted_count"] == 2
        assert nutrition["total_count"] == 3
        assert nutrition["uncounted"] == {"no_food": 1}
    finally:
        _set_mode("simple")


def test__recipe_detail__PortionsMustSurviveTheRepositoryPath(api):
    """A banana priced by the piece is only convertible via its portion row.
    If the portion query came back empty the rollup would report the whole
    recipe unconvertible — which is exactly what a missed join looks like."""
    foods = _seed_foods()
    _set_mode("complex")
    try:
        recipe_id = _make_recipe([
            {"stock_item_id": _linked_item("Banana", foods["banana"]),
             "quantity": 3, "unit": None},
        ])

        nutrition = _detail(recipe_id)["nutrition"]

        assert nutrition["counted_count"] == 1
        assert nutrition["uncounted"] == {}
        # No servings typed in, so the figure is for the whole recipe and
        # says so rather than dividing by a guess.
        assert nutrition["basis"] == "recipe"
        assert nutrition["kcal"] == round(3 * 89)
        assert nutrition["protein_g"] == round(3 * 1.09, 1)
    finally:
        _set_mode("simple")


def test__recipe_detail__SimpleMode__OmitsTheRollupEntirely(api):
    foods = _seed_foods()
    _set_mode("simple")
    recipe_id = _make_recipe([
        {"stock_item_id": _linked_item("Flour", foods["flour"]),
         "quantity": 100, "unit": "g"},
    ])

    # Simple mode's whole nutrition feature is the typed `kcal` field; a
    # rollup here would be a second, contradicting number.
    assert _detail(recipe_id)["nutrition"] is None


def _list_row(recipe_id: str) -> dict:
    rows = requests.get(f"{RECIPES}?limit=500").json()["items"]
    return next(r for r in rows if r["recipe_id"] == recipe_id)


def test__recipe_list__ComplexMode__CarriesTheSameRollupAsTheDetail(api):
    """FU-637 — the cookbook card and the "≤ N kcal" filter both read the list
    row, so the two endpoints must agree exactly."""
    foods = _seed_foods()
    _set_mode("complex")
    try:
        recipe_id = _make_recipe(
            [{"stock_item_id": _linked_item("Flour", foods["flour"]),
              "quantity": 400, "unit": "g"}],
            servings=4,
        )

        assert _list_row(recipe_id)["nutrition"] == _detail(recipe_id)["nutrition"]
    finally:
        _set_mode("simple")


def test__recipe_list__SimpleMode__OmitsTheRollup(api):
    foods = _seed_foods()
    _set_mode("simple")
    recipe_id = _make_recipe([
        {"stock_item_id": _linked_item("Flour", foods["flour"]),
         "quantity": 100, "unit": "g"},
    ])

    assert _list_row(recipe_id)["nutrition"] is None


def test__recipe_list__ThinCoverage__IsShownButNotMarkedReliable(api):
    """A recipe we can only account for a fraction of still shows its number
    (with coverage) — but `is_reliable` is false, so a calorie filter won't
    exclude it on the strength of a guess."""
    foods = _seed_foods()
    _set_mode("complex")
    try:
        recipe_id = _make_recipe([
            {"stock_item_id": _linked_item("Flour", foods["flour"]),
             "quantity": 100, "unit": "g"},
            {"stock_item_id": _linked_item("Salt", None), "quantity": 5, "unit": "g"},
            {"stock_item_id": _linked_item("Pepper", None), "quantity": 5, "unit": "g"},
        ])

        nutrition = _list_row(recipe_id)["nutrition"]

        assert nutrition["kcal"] is not None
        assert (nutrition["counted_count"], nutrition["total_count"]) == (1, 3)
        assert nutrition["is_reliable"] is False
    finally:
        _set_mode("simple")


def test__recipe_list__FullCoverage__IsMarkedReliable(api):
    foods = _seed_foods()
    _set_mode("complex")
    try:
        recipe_id = _make_recipe([
            {"stock_item_id": _linked_item("Flour", foods["flour"]),
             "quantity": 100, "unit": "g"},
            {"stock_item_id": _linked_item("Banana", foods["banana"]),
             "quantity": 1, "unit": None},
        ])

        assert _list_row(recipe_id)["nutrition"]["is_reliable"] is True
    finally:
        _set_mode("simple")


def test__recipe_list__RollupCostsAFixedNumberOfQueries(api):
    """The rollup must batch across the page.

    `test_recipes_query_count` (FU-138) guards the rest of the handler, but it
    creates recipes with **no ingredients** — which is exactly the input the
    rollup short-circuits on, so an N+1 in here would sail past it. This adds
    recipes that each carry a food-linked ingredient, and pins the same
    "adding recipes must not add ≈N selects" ratio that test uses.
    """
    from tests.e2e.dora_api._query_counter import SelectCounter

    foods = _seed_foods()
    _set_mode("complex")
    try:
        for index in range(8):
            _make_recipe([{
                "stock_item_id": _linked_item(f"Flour {index}", foods["flour"]),
                "quantity": 100, "unit": "g",
            }])

        with SelectCounter() as few:
            small = requests.get(f"{RECIPES}?limit=2").json()["items"]
        with SelectCounter() as many:
            large = requests.get(f"{RECIPES}?limit=500").json()["items"]

        extra_recipes = len(large) - len(small)
        assert extra_recipes >= 8, "seeding didn't produce enough recipes to be meaningful"
        # Same budget as FU-138: a batched lookup may add a few IN-list shards,
        # never ≈1 select per recipe.
        assert (many.count - few.count) <= 0.5 * extra_recipes, (few.count, many.count, extra_recipes)
    finally:
        _set_mode("simple")
