"""The per-100g nutrient table on the stock-item detail DTO.

Owner request 2026-08-17: "what other nutrition data can be pulled? Possible to
have an optional section at the bottom for potassium, vitamin D, calcium, iron?"
— which added a `more` group alongside the standard `panel`.

The table is now *rendered server-side* (`nutrition/nutrients.display_rows`):
labels, order, units, rounding and the panel/more split all live in one module,
where they used to be duplicated into the SPA by hand. That makes the DTO the
contract worth pinning — it's what stops a nutrient being added to the importer
and silently never appearing, and it's cheap to check here versus eyeballing a
detail page.

The `nutrient_rows` shape is deliberately strict about *absence*: a nutrient the
source didn't state has no row at all. Rendering it as `0` would be inventing a
fact about someone's food (P12 No-invent), and every source is sparse.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import requests

from dora_api.app import app
from dora_api.domain.entities.app_setting import NUTRITION_MODE_COMPLEX
from dora_api.domain.entities.nutrition_food import (
    NUTRITION_SOURCE_USDA_SR_LEGACY, NutritionFood,
)
from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"


def _set_mode(mode: str) -> str:
    with app.app_context():
        repo = SqlAlchemyRepository()
        setting = get_or_create_app_setting(repo)
        previous = setting.nutrition_mode
        setting.nutrition_mode = mode
        setting.nutrition_off_lookup_enabled = False
        setting.nutrition_usda_api_key = ""
        repo.save_changes()
    return previous


@pytest.fixture
def complex_mode():
    previous = _set_mode(NUTRITION_MODE_COMPLEX)
    yield
    _set_mode(previous)


def _seed_food(**nutrients: float) -> str:
    with app.app_context():
        repo = SqlAlchemyRepository()
        food = NutritionFood(
            id=uuid4(), source=NUTRITION_SOURCE_USDA_SR_LEGACY,
            source_ref=f"s-{uuid4().hex[:8]}", name="Nutrient table subject",
            imported_at=datetime.now(timezone.utc), **nutrients,
        )
        repo.add(food)
        repo.save_changes()
        return str(food.id)


def _linked_food(**nutrients: float) -> dict:
    food_id = _seed_food(**nutrients)
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    item_id = make_stock_item(
        stock_level_id=levels[0]["stock_level_id"],
        name=f"Nutrient subject {uuid4().int % 1_000_000}",
    )["stock_item_id"]
    resp = requests.patch(
        f"{BASE}/stock-items/{item_id}", json={"nutrition_food_id": food_id},
    )
    assert resp.status_code in (200, 204), resp.text
    detail = requests.get(f"{BASE}/stock-items/{item_id}/detail").json()
    return detail["nutrition_food"]


def _labels(rows: list[dict], group: str) -> list[str]:
    return [row["label"] for row in rows if row["group"] == group]


def _value(rows: list[dict], label: str) -> str:
    return next(row["value"] for row in rows if row["label"] == label)


def test__panel_rows__are_ordered_and_worded_like_a_printed_panel(api, complex_mode):
    food = _linked_food(
        kcal_per_100g=88.7, protein_g_per_100g=1.09,
        fat_g_per_100g=0.33, saturated_fat_g_per_100g=0.112,
        carbs_g_per_100g=22.84, sugars_g_per_100g=12.23,
        fibre_g_per_100g=2.6, sodium_mg_per_100g=1.4,
    )

    rows = food["nutrient_rows"]
    assert _labels(rows, "panel") == [
        "Energy", "Protein", "Fat, total", "Saturated",
        "Carbohydrate", "Sugars", "Dietary fibre", "Sodium",
    ]
    # Fat before carbohydrate, each followed by its own sub-row — the order a
    # pack prints, which the old client-side list did not follow.
    assert [row["indent"] for row in rows if row["group"] == "panel"] == [
        False, False, False, True, False, True, False, False,
    ]


def test__values__carry_their_unit_and_the_rounding_a_reader_expects(api, complex_mode):
    food = _linked_food(
        kcal_per_100g=88.7, protein_g_per_100g=1.09,
        fibre_g_per_100g=2.6, sodium_mg_per_100g=1.4,
        potassium_mg_per_100g=358.0, vitamin_d_ug_per_100g=2.0,
    )

    rows = food["nutrient_rows"]
    # Nobody reads a fraction of a kilocalorie or a milligram of sodium.
    assert _value(rows, "Energy") == "89 kcal"
    assert _value(rows, "Sodium") == "1 mg"
    assert _value(rows, "Potassium") == "358 mg"
    # One decimal where the fraction is a real difference — and no trailing
    # ".0" when it isn't.
    assert _value(rows, "Protein") == "1.1 g"
    assert _value(rows, "Dietary fibre") == "2.6 g"
    assert _value(rows, "Vitamin D") == "2 µg"


def test__vitamins_and_minerals__are_their_own_group(api, complex_mode):
    food = _linked_food(
        kcal_per_100g=89.0,
        potassium_mg_per_100g=358.0, calcium_mg_per_100g=5.0,
        iron_mg_per_100g=0.26, vitamin_c_mg_per_100g=8.7,
        vitamin_d_ug_per_100g=0.0, folate_ug_per_100g=20.0,
    )

    rows = food["nutrient_rows"]
    more = _labels(rows, "more")
    assert more == [
        "Potassium", "Calcium", "Iron", "Vitamin C", "Vitamin D", "Folate",
    ]
    # A real zero the source *did* state is kept — it's a fact, unlike a
    # missing value.
    assert _value(rows, "Vitamin D") == "0 µg"
    # The panel block is unaffected by what the optional block knows.
    assert _labels(rows, "panel") == ["Energy"]


def test__unknown_nutrients__have_no_row_at_all(api, complex_mode):
    # A food the source knew almost nothing about — the common case for
    # Open Food Facts entries and older SR Legacy rows.
    food = _linked_food(kcal_per_100g=250.0)

    rows = food["nutrient_rows"]
    assert [row["label"] for row in rows] == ["Energy"]
    # No "more" block to disclose, so the UI drops the whole affordance.
    assert _labels(rows, "more") == []
    # Energy stays a first-class number as well as a formatted row: the
    # summary line above the table renders it on its own.
    assert food["kcal_per_100g"] == 250.0
