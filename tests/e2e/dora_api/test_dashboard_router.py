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

from tests.factories import make_stock_item

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
    # FU-826 — the payload is exactly what a surface renders, no more. Seven
    # fields were dropped here (`products` and `meals` whole, plus
    # `shopping_lists.total_items` and `recipes.{favourites, cookable_count,
    # needs_linking_count}`): they backed counter cards the dashboard rebuild's
    # Phase 1 deleted, and grepping both consumers — DashboardPage and
    # AboutSettings — found no reader for any of them. Asserting the keys
    # *exactly* is deliberate: it is what stops the payload growing a field
    # nothing renders again.
    _Body = _summary()

    assert _Body.keys() == {
        "stock_items", "shopping_lists", "recipes", "meal_plan",
    }
    assert _Body["stock_items"].keys() == {"total", "out_of_stock", "low_stock"}
    assert _Body["shopping_lists"].keys() == {"total"}
    assert _Body["recipes"].keys() == {"total"}
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


#endregion stock / product cards

#region ---------------- recipe card ----------------

# FU-826 removed three tests here along with the fields they asserted:
#   • CreatingProduct → products.total       (sub-object dropped, no consumer)
#   • CookableRecipe  → recipes.cookable_count        (dropped, no consumer)
#   • FavouritingRecipe → recipes.favourites          (dropped, no consumer)
# The cookability *rule* is still exercised — by the per-entry `missing_count`
# and `unlinked_ingredient_count` on upcoming meal-plan entries below, which is
# the only place the dashboard consumes it. The recipe-level cookability
# contract belongs to the recipes router's own suite, not this one.


def test__dashboard_summary__CreatingRecipe__RecipeTotalIncreases(api):
    # `recipes.total` survives the FU-826 trim: AboutSettings' at-a-glance block
    # renders it, and the dashboard hero reads it for the empty-cookbook nudge.
    _Before = _summary()["recipes"]["total"]

    _make_recipe("Dashboard Recipe Total")

    assert _summary()["recipes"]["total"] == _Before + 1

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


def test__dashboard_summary__UpcomingEntries__AreOrderedByDayThenSlotSequence(api):
    """Owner 2026-09-08: *"dessert should not appear before breakfast"*.

    The sort used to be `(scheduled_for, slot)` — the slot **name** — so within
    a day the order was alphabetical and Dessert genuinely preceded Dinner and
    Lunch. It now reads the household's configured slot `sequence`.

    Worth automating despite the manual-first stance: the card shows a
    three-row slice, so on most days the mis-ordering is simply invisible, and
    reproducing it by hand means planning several slots on one day and reading
    a truncated list.
    """
    _Today = _household_today()
    _Recipe = _make_recipe("Dashboard Slot Order")
    _Slots = requests.get(f"{BASE}/meal-slots").json()
    assert len(_Slots) >= 2, "need at least two slots to have an order at all"
    # Sequence order is the expectation; feed them in REVERSE so a stable sort
    # or an insertion-order accident can't pass this by luck.
    _Ordered = sorted(_Slots, key=lambda s: (s["sequence"], s["name"].lower()))
    _Day = (_Today + timedelta(days=3)).isoformat()

    _CreateResponse = requests.post(MEAL_PLANS, json={
        "start_date": _Today.isoformat(),
        "entries": [
            {
                "recipe_id": _Recipe["recipe_id"],
                "scheduled_for": _Day,
                "slot": slot["name"],
            }
            for slot in reversed(_Ordered)
        ],
    })
    assert _CreateResponse.status_code == 201, _CreateResponse.text

    _OnTheDay = [
        e for e in _summary()["meal_plan"]["upcoming_entries"]
        if e["recipe_id"] == _Recipe["recipe_id"] and e["scheduled_for"] == _Day
    ]
    assert [e["slot"] for e in _OnTheDay] == [s["name"] for s in _Ordered]


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


def test__dashboard_summary__UpcomingEntryWithUnlinkedIngredient__ReportsCountAndNullMissing(api):
    # IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — the OTHER null flavour. An entry whose
    # recipe has an unlinked required ingredient is tri-state None for
    # `missing_count` but reports a non-zero `unlinked_ingredient_count`, which
    # is how the "Next to cook" card renders "N to link" rather than the
    # ambiguous "No ingredients".
    #
    # Converted from the old `needs_linking_count` test (FU-826): the
    # collection-wide sum was dropped for having no consumer, but the per-entry
    # field it was derived from is live and drives the badge, so the coverage
    # moved here rather than being deleted with the field.
    _Today = _household_today()
    _Recipe = _make_recipe("Dashboard Unlinked Upcoming", ingredients=[
        {"raw_text": "2 cups mystery flour"},
    ])
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
    assert _Entry["unlinked_ingredient_count"] == 1
    assert _Entry["missing_count"] is None


def test__dashboard_summary__UpcomingEntryInCookBatch__CarriesWholeBatchYield(api):
    # Owner 2026-09-05 — the "Next to cook" card prints this figure and opens
    # cook mode at it, the same as the planner's chips. The summing happens
    # over the whole batch, so a batch that starts before the dashboard's
    # window or runs past it still reports its true yield; the window is what
    # this pins, since folding only the days on screen is the easy wrong answer.
    _Today = _household_today()
    _Recipe = _make_recipe("Dashboard Batch Upcoming")
    _Slot = requests.get(f"{BASE}/meal-slots").json()[0]["name"]

    # Days 0, 1 and 8 — the last one past the summary's seven-day window. (The
    # symmetric case, a member *before* today, can't be built: the write path
    # rejects entries scheduled in the past.)
    _CreateResponse = requests.post(MEAL_PLANS, json={
        "start_date": _Today.isoformat(),
        "entries": [{
            "recipe_id": _Recipe["recipe_id"],
            "scheduled_for": (_Today + timedelta(days=d)).isoformat(),
            "servings": 2,
            "slot": _Slot,
            "cook_key": "dash-batch",
        } for d in (0, 1, 8)],
    })
    assert _CreateResponse.status_code == 201, _CreateResponse.text

    _Entry = next(
        e for e in _summary()["meal_plan"]["upcoming_entries"]
        if e["recipe_id"] == _Recipe["recipe_id"]
    )
    assert _Entry["servings"] == 2, "the entry's own share is untouched"
    assert _Entry["cook_batch_total_servings"] == 6, "3 linked days x 2 servings"


def test__dashboard_summary__StandaloneUpcomingEntry__HasNoBatchYield(api):
    # The common case, and the reason the SPA's `?? entry.servings` fallback
    # exists: a meal that isn't linked to anything reports null, not its own
    # servings dressed up as a batch.
    _Today = _household_today()
    _Recipe = _make_recipe("Dashboard Standalone Upcoming")
    _Slot = requests.get(f"{BASE}/meal-slots").json()[0]["name"]

    _CreateResponse = requests.post(MEAL_PLANS, json={
        "start_date": _Today.isoformat(),
        "entries": [{
            "recipe_id": _Recipe["recipe_id"],
            "scheduled_for": _Today.isoformat(),
            "servings": 4,
            "slot": _Slot,
        }],
    })
    assert _CreateResponse.status_code == 201, _CreateResponse.text

    _Entry = next(
        e for e in _summary()["meal_plan"]["upcoming_entries"]
        if e["recipe_id"] == _Recipe["recipe_id"]
    )
    assert _Entry["servings"] == 4
    assert _Entry["cook_batch_total_servings"] is None

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
    # Owner review 2026-09-04 — `runouts` and `stocktake` were cut (both scored
    # app diligence, not kitchen health); `plan_adherence` and `plan_coverage`
    # replaced them. The closed set itself is pinned in `test_dora_score.py`;
    # here we only check the wire never carries a key outside it.
    _ValidKeys = {"waste", "budget", "freshness", "plan_adherence", "plan_coverage"}
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
