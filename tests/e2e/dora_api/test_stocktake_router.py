"""FU-519 item 2 — stocktake HTTP lifecycle e2e
(`dora_api/features/stocktake/stocktake.py`).

  GET  /api/stocktake/queue                       — overdue items
  POST /api/stock-items/<id>/check                — confirm level (bumps
                                                    last_checked_at, clears Push)
  POST /api/stock-items/<id>/snooze               — Push 3 days
  POST /api/stocktake/bulk-check                  — body {ids}
  POST /api/shopping-lists/<id>/review/complete   — ticked lines → Stocked

The band/auto-tuning *logic* is unit-tested in `tests/test_stocktake_cadence.py`
— this file drives the HTTP lifecycle only. A fresh item's overdue baseline is
its creation moment (grace period = one band), so tests that need an overdue
item backdate `last_checked_at` via targeted SQL (the sanctioned state-setup
escape hatch, see `tests/support.uuid_bind`).
"""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import requests
from sqlalchemy import text

from dora_api.app import app, db
from tests.factories import make_stock_item
from tests.support import assert_problem, uuid_bind

BASE = "http://localhost:5170/api"
QUEUE = f"{BASE}/stocktake/queue"
BULK_CHECK = f"{BASE}/stocktake/bulk-check"

QUEUE_ITEM_KEYS = {
    "stock_item_id", "name", "stock_level_name", "stock_location_name",
    "cadence_band", "cadence_days", "last_checked_at", "overdue_days",
}


#region ---------------- helpers ----------------


def _token() -> str:
    return f"zqs{uuid4().hex[:8]}"


def _stocked_level_id() -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l for l in levels if l["sequence"] == 0)["stock_level_id"]


def _queue_ids(limit: int = 500) -> dict[str, dict]:
    resp = requests.get(QUEUE, params={"limit": limit})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == {"items", "total"}
    return {item["stock_item_id"]: item for item in body["items"]}


def _unmute(stock_item_id: str) -> None:
    """Pin the Mute off explicitly. API-created items are born *unmuted*
    since 2026-08-17 (`stocktake_alerts_are_enabled=True` in
    create_stock_item.py), so this is now a guarantee rather than a flip —
    kept so these tests state the precondition they rely on instead of
    inheriting it from a default that has already moved once."""
    resp = requests.patch(
        f"{BASE}/stock-items/{stock_item_id}",
        json={"stocktake_alerts_are_enabled": True},
    )
    assert resp.status_code == 204, resp.text


def _backdate_last_checked(stock_item_id: str, days_ago: int) -> None:
    past = datetime.now(UTC) - timedelta(days=days_ago)
    with app.app_context(), db.engine.begin() as conn:
        conn.execute(
            text('UPDATE "StockItem" SET last_checked_at = :ts WHERE id = :id'),
            {
                "ts": past.replace(tzinfo=None).isoformat(" "),
                "id": uuid_bind(stock_item_id),
            },
        )


def _overdue_item(name: str, *, days_ago: int = 20) -> str:
    """An unmuted Stocked item last touched `days_ago` days ago — past the
    default fortnightly band (14d), so it queues with overdue = days_ago - 14."""
    item = make_stock_item(stock_level_id=_stocked_level_id(), name=name)
    _unmute(item["stock_item_id"])
    _backdate_last_checked(item["stock_item_id"], days_ago)
    return item["stock_item_id"]


#endregion helpers

#region ---------------- queue ----------------


def test__get_stocktake_queue__FreshItem__GracePeriodKeepsItOut(api):
    item = make_stock_item(stock_level_id=_stocked_level_id(), name=f"{_token()} salt")
    _unmute(item["stock_item_id"])

    queued = _queue_ids()

    # Baseline = creation moment; a brand-new item has a full band of grace,
    # never "top of the queue on turn zero".
    assert item["stock_item_id"] not in queued


def test__get_stocktake_queue__ItemPastFortnightlyBand__QueuedWithOverdueDays(api):
    token = _token()
    item_id = _overdue_item(f"{token} flour", days_ago=20)

    queued = _queue_ids()

    entry = queued[item_id]
    assert set(entry.keys()) == QUEUE_ITEM_KEYS
    assert entry["name"] == f"{token} flour"
    assert entry["cadence_band"] == "fortnightly"  # baseline default band
    assert entry["cadence_days"] == 14
    assert entry["overdue_days"] == 6  # 20 days elapsed - 14 day band
    assert entry["last_checked_at"] is not None
    assert entry["stock_level_name"] is not None


def test__get_stocktake_queue__EssentialItem__BandBumpedOneStepFaster(api):
    token = _token()
    item = make_stock_item(
        stock_level_id=_stocked_level_id(), name=f"{token} coffee", is_essential=True,
    )
    _unmute(item["stock_item_id"])
    _backdate_last_checked(item["stock_item_id"], 10)

    queued = _queue_ids()

    # Essential bumps fortnightly → weekly; 10 days elapsed - 7 = 3 overdue.
    entry = queued[item["stock_item_id"]]
    assert entry["cadence_band"] == "weekly"
    assert entry["cadence_days"] == 7
    assert entry["overdue_days"] == 3


def test__get_stocktake_queue__InvalidLimit__BadRequest(api):
    assert_problem(
        requests.get(QUEUE, params={"limit": "soon"}), 400,
        title="limit must be an integer.",
    )
    assert_problem(
        requests.get(QUEUE, params={"limit": 0}), 400,
        title="limit must be between 1 and 500.",
    )
    assert_problem(
        requests.get(QUEUE, params={"limit": 501}), 400,
        title="limit must be between 1 and 500.",
    )


#endregion queue

#region ---------------- check ----------------


def test__check_stock_item__OverdueItem__LeavesQueue(api):
    item_id = _overdue_item(f"{_token()} sugar")
    assert item_id in _queue_ids()

    resp = requests.post(f"{BASE}/stock-items/{item_id}/check")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["stock_item_id"] == item_id
    assert body["last_checked_at"] is not None
    assert item_id not in _queue_ids()


def test__check_stock_item__UnknownItem__NotFound(api):
    missing_id = uuid4()

    resp = requests.post(f"{BASE}/stock-items/{missing_id}/check")

    assert_problem(
        resp, 404, detail=f"StockItem with the ID '{missing_id}' was not found.",
    )


#endregion check

#region ---------------- snooze (Push) ----------------


def test__snooze_stock_item__OverdueItem__ThreeDayPushWithoutCheckClaim(api):
    item_id = _overdue_item(f"{_token()} pasta")
    assert item_id in _queue_ids()
    before = requests.get(
        f"{BASE}/stock-items", params={"filter": f"stock_item_id:eq:{item_id}"},
    ).json()["items"][0]

    resp = requests.post(f"{BASE}/stock-items/{item_id}/snooze")

    assert resp.status_code == 200, resp.text
    snoozed_until = datetime.fromisoformat(resp.json()["snoozed_until"])
    delta = snoozed_until - datetime.now(UTC).replace(tzinfo=snoozed_until.tzinfo)
    assert timedelta(days=2, hours=23) < delta <= timedelta(days=3)
    # Push makes no claim the stock is right — last_checked_at untouched.
    after = requests.get(
        f"{BASE}/stock-items", params={"filter": f"stock_item_id:eq:{item_id}"},
    ).json()["items"][0]
    assert after["last_checked_at"] == before["last_checked_at"]


def test__snooze_stock_item__SnoozedOverdueItem__HiddenFromQueue(api):
    # Regression for the FU-526 fix (2026-07-12): an active snooze made
    # resolve_overdue_map compare a tz-naive (SQLite) snoozed_until against a
    # tz-aware now_ → TypeError → GET /api/stocktake/queue 500'd. `_queue_ids`
    # asserts the 200, so this now proves the queue survives an active snooze.
    item_id = _overdue_item(f"{_token()} noodles")
    assert requests.post(f"{BASE}/stock-items/{item_id}/snooze").status_code == 200

    assert item_id not in _queue_ids()

    # The alerts feed shares resolve_overdue_map, so the same TypeError broke
    # the alerts bell while any snooze was active. Confirm it stays healthy.
    alerts = requests.get(f"{BASE}/alerts")
    assert alerts.status_code == 200, alerts.text


def test__snooze_stock_item__ThenCheck__CheckClearsTheSnooze(api):
    item_id = _overdue_item(f"{_token()} lentils")
    assert requests.post(f"{BASE}/stock-items/{item_id}/snooze").status_code == 200

    check = requests.post(f"{BASE}/stock-items/{item_id}/check")

    assert check.status_code == 200, check.text
    # A Check is a stronger claim than a Push; snooze is gone and the item
    # stays out of the queue on the *checked* baseline instead.
    _backdate_last_checked(item_id, 20)
    assert item_id in _queue_ids()


def test__snooze_stock_item__UnknownItem__NotFound(api):
    missing_id = uuid4()

    resp = requests.post(f"{BASE}/stock-items/{missing_id}/snooze")

    assert_problem(
        resp, 404, detail=f"StockItem with the ID '{missing_id}' was not found.",
    )


#endregion snooze

#region ---------------- bulk-check ----------------


def test__bulk_check__TwoOverdueItems__BothCheckedAndDequeued(api):
    token = _token()
    first = _overdue_item(f"{token} oats")
    second = _overdue_item(f"{token} honey")

    resp = requests.post(BULK_CHECK, json={"ids": [first, second]})

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"checked": 2}
    queued = _queue_ids()
    assert first not in queued
    assert second not in queued


def test__bulk_check__UnknownIds__CountsZeroRows(api):
    resp = requests.post(BULK_CHECK, json={"ids": [str(uuid4())]})

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"checked": 0}


def test__bulk_check__EmptyIds__ValidationFailure(api):
    resp = requests.post(BULK_CHECK, json={"ids": []})

    assert_problem(resp, 400, field="ids")


#endregion bulk-check

#region ---------------- shopping-list review/complete ----------------


def _item_dto(stock_item_id: str) -> dict:
    return requests.get(
        f"{BASE}/stock-items", params={"filter": f"stock_item_id:eq:{stock_item_id}"},
    ).json()["items"][0]


def test__review_complete__TickedLine__ItemSetStockedAndChecked(api):
    token = _token()
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    out_level = next(l for l in levels if l["sequence"] == 2)
    stocked_level = next(l for l in levels if l["sequence"] == 0)
    item = make_stock_item(
        stock_level_id=out_level["stock_level_id"], name=f"{token} butter",
    )
    list_id = requests.post(
        f"{BASE}/shopping-lists", json={"name": f"{token} review"},
    ).json()["shopping_list_id"]
    line = requests.post(
        f"{BASE}/shopping-lists/{list_id}/lines",
        json={"stock_item_id": item["stock_item_id"]},
    )
    assert line.status_code in (200, 201), line.text
    line_id = requests.get(f"{BASE}/shopping-lists/{list_id}").json()["lines"][0]["line_id"]
    tick = requests.patch(
        f"{BASE}/shopping-lists/{list_id}/lines/{line_id}", json={"is_ticked": True},
    )
    assert tick.status_code == 204, tick.text

    resp = requests.post(f"{BASE}/shopping-lists/{list_id}/review/complete", json={})

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"set_stocked": 1, "checked": 1}
    after = _item_dto(item["stock_item_id"])
    assert after["stock_level_id"] == stocked_level["stock_level_id"]
    assert after["last_checked_at"] is not None


def test__review_complete__NoTickedLines__CountsZero(api):
    list_id = requests.post(
        f"{BASE}/shopping-lists", json={"name": f"{_token()} untouched"},
    ).json()["shopping_list_id"]

    resp = requests.post(f"{BASE}/shopping-lists/{list_id}/review/complete", json={})

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"set_stocked": 0, "checked": 0}


def test__review_complete__UnknownList__NotFound(api):
    missing_id = uuid4()

    resp = requests.post(f"{BASE}/shopping-lists/{missing_id}/review/complete", json={})

    assert_problem(
        resp, 404, detail=f"ShoppingList with the ID '{missing_id}' was not found.",
    )


#endregion review/complete
