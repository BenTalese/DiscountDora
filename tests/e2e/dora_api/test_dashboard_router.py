"""FU-519 / PROPOSAL_TEST_SUITE_IMPROVEMENTS §5.D — dashboard router e2e coverage.

GET /api/dashboard/summary (the single aggregated payload every card
reads from) and GET /api/dashboard/dora-score (P8-08). Each aggregate is
verified delta-style: snapshot the summary, create data through the real
endpoints, assert the right counter moved — so seeded rows never leak
into the expectations. The household-tz anchoring of the upcoming window
itself is already pinned by test_household_tz_boundaries.py; here we
only place entries relative to the API's own today anchor.
"""
from datetime import date, timedelta
from uuid import uuid4

import requests

from tests.factories import make_product, make_stock_item

BASE = "http://localhost:5170/api"
SUMMARY = f"{BASE}/dashboard/summary"
DORA_SCORE = f"{BASE}/dashboard/dora-score"
RECIPES = f"{BASE}/recipes"
MEAL_PLANS = f"{BASE}/meal-plans"

#region ---------------- setup ----------------


def _summary() -> dict:
    resp = requests.get(SUMMARY)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _stock_level_id(sequence: int) -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == sequence)


def _household_today() -> date:
    return date.fromisoformat(
        requests.get(f"{MEAL_PLANS}/today").json()["today"]
    )


def _make_recipe(name_prefix: str = "Dashboard Recipe", **body) -> dict:
    resp = requests.post(RECIPES, json={
        "name": f"{name_prefix} {uuid4().hex[:8]}", **body,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()

#endregion setup

#region ---------------- summary shape ----------------


def test__dashboard_summary__ResponseShape__CarriesEveryCardPayload(api):
    _Body = _summary()

    assert _Body.keys() == {
        "stock_items", "shopping_lists", "products", "recipes", "meals", "meal_plan",
    }
    assert _Body["stock_items"].keys() == {"total", "out_of_stock", "low_stock"}
    assert _Body["shopping_lists"].keys() == {"total", "total_items"}
    assert _Body["products"].keys() == {"total"}
    assert _Body["recipes"].keys() == {
        "total", "favourites", "cookable_count", "needs_linking_count",
    }
    assert _Body["meals"].keys() == {"total_definitions", "total_in_stock"}
    assert _Body["meal_plan"].keys() == {"upcoming_entries"}
    assert isinstance(_Body["meal_plan"]["upcoming_entries"], list)

#endregion summary shape

#region ---------------- stock / product cards ----------------


def test__dashboard_summary__CreatingOutOfStockItem__TotalAndOutCountsIncrease(api):
    _Before = _summary()["stock_items"]

    make_stock_item(
        stock_level_id=_stock_level_id(2),
        name=f"Dashboard Out Item {uuid4().hex[:8]}",
    )

    _After = _summary()["stock_items"]
    assert _After["total"] == _Before["total"] + 1
    assert _After["out_of_stock"] == _Before["out_of_stock"] + 1
    assert _After["low_stock"] == _Before["low_stock"]


def test__dashboard_summary__CreatingLowStockItem__LowCountIncreases(api):
    _Before = _summary()["stock_items"]

    make_stock_item(
        stock_level_id=_stock_level_id(1),
        name=f"Dashboard Low Item {uuid4().hex[:8]}",
    )

    _After = _summary()["stock_items"]
    assert _After["total"] == _Before["total"] + 1
    assert _After["low_stock"] == _Before["low_stock"] + 1
    assert _After["out_of_stock"] == _Before["out_of_stock"]


def test__dashboard_summary__CreatingProduct__ProductTotalIncreases(api):
    _Before = _summary()["products"]["total"]

    make_product(
        name=f"Dashboard Product {uuid4().hex[:8]}",
        merchant_stockcode=uuid4().hex[:10],
    )

    assert _summary()["products"]["total"] == _Before + 1

#endregion stock / product cards

#region ---------------- recipe card ----------------


def test__dashboard_summary__FavouritingRecipe__FavouritesCountIncreases(api):
    _Before = _summary()["recipes"]
    _Recipe = _make_recipe("Dashboard Favourite")

    _MidTotal = _summary()["recipes"]["total"]
    assert _MidTotal == _Before["total"] + 1

    assert requests.patch(
        f"{RECIPES}/{_Recipe['recipe_id']}", json={"is_favourite": True},
    ).status_code == 204

    _After = _summary()["recipes"]
    assert _After["favourites"] == _Before["favourites"] + 1


def test__dashboard_summary__CookableRecipe__CookableCountIncreases(api):
    _Before = _summary()["recipes"]["cookable_count"]
    _Item = make_stock_item(
        stock_level_id=_stock_level_id(0),
        name=f"Dashboard Stocked Ing {uuid4().hex[:8]}",
    )

    _make_recipe("Dashboard Cookable", ingredients=[
        {"stock_item_id": _Item["stock_item_id"]},
    ])

    assert _summary()["recipes"]["cookable_count"] == _Before + 1


def test__dashboard_summary__RecipeWithUnlinkedIngredient__NeedsLinkingCountIncreases(api):
    # IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — unlinked recipes are tri-state
    # None: counted under needs_linking, never under cookable.
    _Before = _summary()["recipes"]

    _make_recipe("Dashboard Unlinked", ingredients=[
        {"raw_text": "2 cups mystery flour"},
    ])

    _After = _summary()["recipes"]
    assert _After["needs_linking_count"] == _Before["needs_linking_count"] + 1
    assert _After["cookable_count"] == _Before["cookable_count"]

#endregion recipe card

#region ---------------- meal-plan card ----------------


def test__dashboard_summary__EntryScheduledWithinWeek__AppearsInUpcomingEntries(api):
    _Today = _household_today()
    _Item = make_stock_item(
        stock_level_id=_stock_level_id(0),
        name=f"Dashboard Upcoming Ing {uuid4().hex[:8]}",
    )
    _Recipe = _make_recipe("Dashboard Upcoming", ingredients=[
        {"stock_item_id": _Item["stock_item_id"]},
    ])
    _Slot = requests.get(f"{BASE}/meal-slots").json()[0]["name"]
    _ScheduledFor = (_Today + timedelta(days=2)).isoformat()

    _CreateResponse = requests.post(MEAL_PLANS, json={
        "start_date": _Today.isoformat(),
        "entries": [{
            "recipe_id": _Recipe["recipe_id"],
            "scheduled_for": _ScheduledFor,
            "servings": 3,
            "slot": _Slot,
        }],
    })
    assert _CreateResponse.status_code == 201, _CreateResponse.text

    _Upcoming = _summary()["meal_plan"]["upcoming_entries"]
    _Entry = next(
        (e for e in _Upcoming if e["recipe_id"] == _Recipe["recipe_id"]), None,
    )
    assert _Entry is not None
    assert _Entry["recipe_name"] == _Recipe["name"]
    assert _Entry["scheduled_for"] == _ScheduledFor
    assert _Entry["slot"] == _Slot
    assert _Entry["servings"] == 3
    # Fully-linked, fully-stocked recipe → ready to cook (0 missing).
    assert _Entry["missing_count"] == 0
    assert _Entry["unlinked_ingredient_count"] == 0


def test__dashboard_summary__UpcomingEntryForEmptyRecipe__MissingCountIsNull(api):
    # Tri-state contract on the "Next to cook" card: a recipe with no
    # ingredients has nothing to evaluate — null, not zero.
    _Today = _household_today()
    _Recipe = _make_recipe("Dashboard Empty Upcoming")
    _Slot = requests.get(f"{BASE}/meal-slots").json()[0]["name"]

    _CreateResponse = requests.post(MEAL_PLANS, json={
        "start_date": _Today.isoformat(),
        "entries": [{
            "recipe_id": _Recipe["recipe_id"],
            "scheduled_for": _Today.isoformat(),
            "slot": _Slot,
        }],
    })
    assert _CreateResponse.status_code == 201, _CreateResponse.text

    _Entry = next(
        e for e in _summary()["meal_plan"]["upcoming_entries"]
        if e["recipe_id"] == _Recipe["recipe_id"]
    )
    assert _Entry["missing_count"] is None
    assert _Entry["unlinked_ingredient_count"] == 0

#endregion meal-plan card

#region ---------------- dora score ----------------


def test__dora_score__AuthenticatedRequest__ReturnsCompositeAndComponentBreakdown(api):
    _Response = requests.get(DORA_SCORE)

    assert _Response.status_code == 200, _Response.text
    _Body = _Response.json()
    assert {"composite", "components", "trend_delta", "trend_direction", "window_days"} <= _Body.keys()
    assert _Body["composite"] is None or 0 <= _Body["composite"] <= 100
    assert isinstance(_Body["window_days"], int) and _Body["window_days"] > 0
    assert isinstance(_Body["components"], list)
    _ValidKeys = {"waste", "budget", "freshness", "runouts", "stocktake"}
    for _Component in _Body["components"]:
        assert {"key", "label", "score", "reason"} <= _Component.keys()
        assert _Component["key"] in _ValidKeys
        assert _Component["score"] is None or 0 <= _Component["score"] <= 100
        assert isinstance(_Component["reason"], str) and _Component["reason"]


def test__dora_score__EveryRequestLogsTheScoreLine__NoNaNNoNegatives(api, caplog):
    # DORA_VERIFY P8-08: each request logs
    # "Dora Score user=… composite=… trend=… (delta=…)" — one line, no
    # exceptions, no NaN, and the composite is never negative.
    import logging
    import re

    with caplog.at_level(logging.INFO, logger="dora_api.features.dashboard.get_dora_score"):
        _Response = requests.get(DORA_SCORE)

    assert _Response.status_code == 200, _Response.text
    _Lines = [r.getMessage() for r in caplog.records if "Dora Score" in r.getMessage()]
    assert len(_Lines) == 1, _Lines
    _Match = re.fullmatch(
        r"Dora Score user=[0-9a-f-]+ composite=(\S+) trend=(up|down|flat|None) \(delta=(\S+)\)",
        _Lines[0],
    )
    assert _Match, _Lines[0]
    _Composite, _, _Delta = _Match.groups()
    assert "nan" not in _Lines[0].lower()
    if _Composite != "None":
        assert 0 <= int(_Composite) <= 100
    # delta may be negative (a falling score) — but never NaN/garbage.
    if _Delta != "None":
        int(_Delta)
    assert not any(r.exc_info for r in caplog.records)

#endregion dora score
