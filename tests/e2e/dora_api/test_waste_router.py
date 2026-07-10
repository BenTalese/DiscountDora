"""FU-519 item 2 — waste router e2e (`dora_api/features/waste/waste.py`).

  GET    /api/waste/rescue            — expiring items + rescue recipe ranking
  POST   /api/waste/events            — log a discard (reason only)
  GET    /api/waste/events?limit=N    — recent waste log
  DELETE /api/waste/events/<id>       — idempotent (Undo toast)
  GET    /api/waste/insights          — {most_wasted, most_recent}

Determinism: expiry dates are derived from the household-today anchor
(`GET /api/meal-plans/today`), never from a local `date.today()` — the
rescue horizon is a household-calendar window (R-021).
"""
from datetime import date, timedelta
from uuid import uuid4

import requests

from tests.factories import make_stock_item
from tests.support import assert_problem, is_valid_uuid

BASE = "http://localhost:5170/api"
RESCUE = f"{BASE}/waste/rescue"
EVENTS = f"{BASE}/waste/events"
INSIGHTS = f"{BASE}/waste/insights"

ITEM_KEYS = {
    "stock_item_id", "name", "expiry_date", "days_until_expiry",
    "is_expired", "stock_level_name", "estimated_value",
}
RECIPE_KEYS = {
    "recipe_id", "name", "cook_time_minutes", "difficulty",
    "matching_expiring_items", "matching_count", "missing_ingredients",
    "is_favourite",
}
EVENT_KEYS = {"event_id", "stock_item_id", "stock_item_name", "reason", "occurred_at"}


#region ---------------- helpers ----------------


def _token() -> str:
    return f"zqw{uuid4().hex[:8]}"


def _household_today() -> date:
    resp = requests.get(f"{BASE}/meal-plans/today")
    assert resp.status_code == 200, resp.text
    return date.fromisoformat(resp.json()["today"])


def _levels_by_sequence() -> dict[int, str]:
    items = requests.get(f"{BASE}/stock-levels").json()["items"]
    return {level["sequence"]: level["stock_level_id"] for level in items}


def _rescue(**params) -> dict:
    resp = requests.get(RESCUE, params=params)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == {"horizon_days", "items", "recipes"}
    return body


def _expiring_item(name: str, days_from_today: int, *, level_id: str) -> dict:
    today = _household_today()
    return make_stock_item(
        stock_level_id=level_id,
        name=name,
        expiry_date=(today + timedelta(days=days_from_today)).isoformat(),
    )


def _log_event(stock_item_id: str, reason: str = "expired") -> str:
    resp = requests.post(EVENTS, json={"stock_item_id": stock_item_id, "reason": reason})
    assert resp.status_code == 200, resp.text
    return resp.json()["event_id"]


#endregion helpers

#region ---------------- rescue feed ----------------


def test__get_waste_rescue__ItemExpiringWithinHorizon__AppearsInFeed(api):
    token = _token()
    levels = _levels_by_sequence()
    item = _expiring_item(f"{token} milk", 3, level_id=levels[0])

    body = _rescue()

    assert body["horizon_days"] == 7
    hits = [i for i in body["items"] if i["stock_item_id"] == item["stock_item_id"]]
    assert len(hits) == 1
    hit = hits[0]
    assert set(hit.keys()) == ITEM_KEYS
    assert hit["name"] == f"{token} milk"
    assert hit["days_until_expiry"] == 3
    assert hit["is_expired"] is False
    assert hit["expiry_date"] == (_household_today() + timedelta(days=3)).isoformat()
    # Stocked level name comes through for the "worth rescuing" framing.
    assert hit["stock_level_name"] is not None


def test__get_waste_rescue__AlreadyExpiredItem__FlaggedExpiredWithNegativeDays(api):
    token = _token()
    levels = _levels_by_sequence()
    item = _expiring_item(f"{token} yoghurt", -2, level_id=levels[0])

    body = _rescue()

    hit = next(i for i in body["items"] if i["stock_item_id"] == item["stock_item_id"])
    assert hit["is_expired"] is True
    assert hit["days_until_expiry"] == -2


def test__get_waste_rescue__ItemBeyondHorizon__ExcludedUntilHorizonWidened(api):
    token = _token()
    levels = _levels_by_sequence()
    item = _expiring_item(f"{token} beans", 10, level_id=levels[0])

    default_ids = {i["stock_item_id"] for i in _rescue()["items"]}
    widened = _rescue(horizon_days=30)

    assert item["stock_item_id"] not in default_ids
    assert widened["horizon_days"] == 30
    assert item["stock_item_id"] in {i["stock_item_id"] for i in widened["items"]}


def test__get_waste_rescue__HorizonOutOfRange__ClampedOrDefaulted(api):
    # Clamp to [0, 60]; a non-numeric value falls back to the 7-day default.
    assert _rescue(horizon_days=999)["horizon_days"] == 60
    assert _rescue(horizon_days=-5)["horizon_days"] == 0
    assert _rescue(horizon_days="soon")["horizon_days"] == 7


def test__get_waste_rescue__RecipesUsingExpiringItems__RankedByMatchCount(api):
    token = _token()
    levels = _levels_by_sequence()
    expiring_a = _expiring_item(f"{token} spinach", 2, level_id=levels[0])
    expiring_b = _expiring_item(f"{token} feta", 2, level_id=levels[0])
    # A required ingredient that's out of stock → missing_ingredients.
    out_item = make_stock_item(stock_level_id=levels[2], name=f"{token} pastry")

    two_match = requests.post(f"{BASE}/recipes", json={
        "name": f"{token} double rescue",
        "ingredients": [
            {"stock_item_id": expiring_a["stock_item_id"]},
            {"stock_item_id": expiring_b["stock_item_id"]},
        ],
    })
    assert two_match.status_code == 201, two_match.text
    one_match = requests.post(f"{BASE}/recipes", json={
        "name": f"{token} single rescue",
        "ingredients": [
            {"stock_item_id": expiring_a["stock_item_id"]},
            {"stock_item_id": out_item["stock_item_id"]},
        ],
    })
    assert one_match.status_code == 201, one_match.text
    bystander = requests.post(f"{BASE}/recipes", json={"name": f"{token} bystander"})
    assert bystander.status_code == 201, bystander.text

    recipes = _rescue()["recipes"]

    by_id = {r["recipe_id"]: r for r in recipes}
    two = by_id[two_match.json()["recipe_id"]]
    one = by_id[one_match.json()["recipe_id"]]
    assert set(two.keys()) == RECIPE_KEYS
    assert two["matching_count"] == 2
    assert sorted(two["matching_expiring_items"]) == sorted(
        [f"{token} spinach", f"{token} feta"]
    )
    assert one["matching_count"] == 1
    assert f"{token} pastry" in one["missing_ingredients"]
    # Most rescues first.
    ordered = [r["recipe_id"] for r in recipes]
    assert ordered.index(two["recipe_id"]) < ordered.index(one["recipe_id"])
    # A recipe touching no at-risk item never appears.
    assert bystander.json()["recipe_id"] not in by_id


#endregion rescue feed

#region ---------------- waste events ----------------


def test__log_waste_event__ValidReason__EventCreatedAndListed(api):
    token = _token()
    levels = _levels_by_sequence()
    item = make_stock_item(stock_level_id=levels[0], name=f"{token} bread")

    event_id = _log_event(item["stock_item_id"], "spoiled")

    assert is_valid_uuid(event_id)
    events = requests.get(EVENTS).json()["events"]
    hit = next(e for e in events if e["event_id"] == event_id)
    assert set(hit.keys()) == EVENT_KEYS
    assert hit["stock_item_id"] == item["stock_item_id"]
    # Name is denormalised at log time so renames/deletes keep history honest.
    assert hit["stock_item_name"] == f"{token} bread"
    assert hit["reason"] == "spoiled"
    assert hit["occurred_at"] is not None


def test__log_waste_event__UnknownReason__BadRequestListsAllowedValues(api):
    levels = _levels_by_sequence()
    item = make_stock_item(stock_level_id=levels[0], name=f"{_token()} jam")

    resp = requests.post(
        EVENTS, json={"stock_item_id": item["stock_item_id"], "reason": "yeeted"},
    )

    assert_problem(resp, 400, title="Invalid reason 'yeeted'")


def test__log_waste_event__UnknownStockItem__NotFound(api):
    missing_id = uuid4()

    resp = requests.post(
        EVENTS, json={"stock_item_id": str(missing_id), "reason": "expired"},
    )

    assert_problem(
        resp, 404, detail=f"StockItem with the ID '{missing_id}' was not found.",
    )


def test__list_waste_events__LimitApplied__NewestFirst(api):
    levels = _levels_by_sequence()
    item = make_stock_item(stock_level_id=levels[0], name=f"{_token()} olives")
    first = _log_event(item["stock_item_id"])
    second = _log_event(item["stock_item_id"])

    limited = requests.get(EVENTS, params={"limit": 1}).json()["events"]
    unlimited = requests.get(EVENTS).json()["events"]

    assert len(limited) == 1
    ordered = [e["event_id"] for e in unlimited]
    # Newest first — the second log outranks the first.
    assert ordered.index(second) < ordered.index(first)


def test__delete_waste_event__RepeatDelete__IdempotentNoContent(api):
    levels = _levels_by_sequence()
    item = make_stock_item(stock_level_id=levels[0], name=f"{_token()} rice")
    event_id = _log_event(item["stock_item_id"])

    first = requests.delete(f"{EVENTS}/{event_id}")
    second = requests.delete(f"{EVENTS}/{event_id}")

    assert first.status_code == 204
    # Undo double-tap / retry: already-gone is still a 204, not an error.
    assert second.status_code == 204
    remaining = requests.get(EVENTS).json()["events"]
    assert event_id not in {e["event_id"] for e in remaining}


def test__delete_waste_event__MalformedId__BadRequest(api):
    resp = requests.delete(f"{EVENTS}/not-a-uuid")

    assert_problem(resp, 400, title="event_id must be a UUID.")


#endregion waste events

#region ---------------- insights ----------------


def test__get_waste_insights__RepeatOffender__RankedByEventCount(api):
    token = _token()
    levels = _levels_by_sequence()
    repeat = make_stock_item(stock_level_id=levels[0], name=f"{token} lettuce")
    once = make_stock_item(stock_level_id=levels[0], name=f"{token} celery")
    _log_event(repeat["stock_item_id"], "spoiled")
    _log_event(repeat["stock_item_id"], "expired")
    newest = _log_event(once["stock_item_id"], "overbought")

    resp = requests.get(INSIGHTS)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == {"window_days", "total_events", "most_wasted", "most_recent"}
    assert body["window_days"] == 90
    assert body["total_events"] >= 3
    buckets = {b["stock_item_id"]: b for b in body["most_wasted"]}
    repeat_bucket = buckets[repeat["stock_item_id"]]
    assert repeat_bucket["event_count"] == 2
    assert repeat_bucket["stock_item_name"] == f"{token} lettuce"
    assert repeat_bucket["last_occurred_at"] is not None
    assert buckets[once["stock_item_id"]]["event_count"] == 1
    # More events ranks strictly higher.
    ranked = [b["stock_item_id"] for b in body["most_wasted"]]
    assert ranked.index(repeat["stock_item_id"]) < ranked.index(once["stock_item_id"])
    # most_recent is newest-first and ungrouped.
    assert body["most_recent"][0]["event_id"] == newest


def test__get_waste_insights__WindowOutOfRange__Clamped(api):
    assert requests.get(INSIGHTS, params={"window_days": 1}).json()["window_days"] == 7
    assert requests.get(INSIGHTS, params={"window_days": 9999}).json()["window_days"] == 365
    assert requests.get(INSIGHTS, params={"window_days": "abc"}).json()["window_days"] == 90


#endregion insights
