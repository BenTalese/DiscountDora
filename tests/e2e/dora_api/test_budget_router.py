"""FU-519 item 2 — budget router e2e (`dora_api/features/budget/budget.py`).

  GET /api/budget/status   — current-period spend / remaining / projection
  GET /api/budget/history  — last N periods for the trend chip

Budget settings live on the User row via `PATCH /api/auth/me`
(`budget_amount` / `budget_period` / `clear_budget_amount`) — exercised here
because the budget endpoints are their read surface.

Determinism: "spent" buckets archived lists by `completed_at` into windows
anchored on household-today (R-021). Finishing a list stamps `completed_at =
now(UTC)`, which near a period boundary can fall *outside* the current
household window — so every test that asserts window membership backdates
`completed_at` to a mid-window instant via targeted SQL (the sanctioned
state-setup escape hatch, see `tests/support.uuid_bind`).
"""
from datetime import date, datetime, time, timedelta

import requests
from sqlalchemy import text

from dora_api.app import app, db
from tests.e2e.dora_api._error_assertions import domain_err
from tests.e2e.dora_api._spend_seeding import seed_purchase
from tests.support import uuid_bind

BASE = "http://localhost:5170/api"
STATUS = f"{BASE}/budget/status"
HISTORY = f"{BASE}/budget/history"
ME = f"{BASE}/auth/me"

STATUS_KEYS = {
    "enabled", "amount", "period", "period_start", "period_end",
    "spent", "projected_active", "remaining", "over_budget",
}
HISTORY_ROW_KEYS = {"period_start", "period_end", "spent", "over_budget"}


#region ---------------- helpers ----------------


def _status() -> dict:
    resp = requests.get(STATUS)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _history(**params) -> list[dict]:
    resp = requests.get(HISTORY, params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()["rows"]


def _set_completed_at(shopping_list_id: str, when: datetime) -> None:
    """Backdate an archived list's completion to a deterministic instant.
    Stored as the naive-UTC string shape the SQLite DateTime column uses."""
    with app.app_context(), db.engine.begin() as conn:
        conn.execute(
            text('UPDATE "ShoppingList" SET completed_at = :ts WHERE id = :id'),
            {
                "ts": when.replace(tzinfo=None).isoformat(" "),
                "id": uuid_bind(shopping_list_id),
            },
        )


def _mid_window(period_start: str) -> datetime:
    """A UTC instant safely inside the half-open window starting at
    ``period_start`` — one day in, at noon (weekly windows are 7 days, so
    start+1d always fits)."""
    start = date.fromisoformat(period_start)
    return datetime.combine(start + timedelta(days=1), time(12, 0))


def _seed_spend_in_current_period(amount: float) -> dict:
    seeded = seed_purchase(actual_unit_price=amount)
    _set_completed_at(seeded["shopping_list_id"], _mid_window(_status()["period_start"]))
    return seeded


#endregion helpers

#region ---------------- status ----------------


def test__get_budget_status__NoBudgetConfigured__DisabledButWindowStillReported(api):
    body = _status()

    assert set(body.keys()) == STATUS_KEYS
    assert body["enabled"] is False
    assert body["amount"] is None
    assert body["remaining"] is None
    assert body["over_budget"] is False
    # The window is computed even when the feature is off — the dashboard
    # shows passive "this week's spend". Default period is weekly.
    assert body["period"] == "weekly"
    start = date.fromisoformat(body["period_start"])
    end = date.fromisoformat(body["period_end"])
    assert (end - start).days == 7
    assert start.weekday() == 0  # Monday-start ISO weeks
    today = date.fromisoformat(
        requests.get(f"{BASE}/meal-plans/today").json()["today"]
    )
    assert start <= today < end


def test__get_budget_status__CompletedShopInsidePeriod__SpentIncludesIt(api):
    spent_before = _status()["spent"]

    _seed_spend_in_current_period(7.0)

    assert _status()["spent"] == round(spent_before + 7.0, 2)


def test__get_budget_status__BudgetSet__RemainingAndOverBudgetDerived(api):
    _seed_spend_in_current_period(7.0)

    patch = requests.patch(ME, json={"budget_amount": 100.0})
    assert patch.status_code == 200, patch.text
    body = _status()

    assert body["enabled"] is True
    assert body["amount"] == 100.0
    assert body["remaining"] == round(100.0 - body["spent"], 2)
    assert body["over_budget"] is False

    # Tighten the budget below the spend → over_budget flips.
    assert requests.patch(ME, json={"budget_amount": 5.0}).status_code == 200
    over = _status()
    assert over["over_budget"] is True
    assert over["remaining"] == round(5.0 - over["spent"], 2)
    assert over["remaining"] < 0


def test__get_budget_status__ActiveListWithPickedPrice__CountsAsProjectedNotSpent(api):
    baseline = _status()

    # Ticked line with a picked snapshot on a list that is never finished.
    seed_purchase(price_now=6.5, finish=False)
    body = _status()

    assert body["projected_active"] == round(baseline["projected_active"] + 6.5, 2)
    assert body["spent"] == baseline["spent"]


def test__patch_me__ClearBudgetAmount__BudgetDisabledAgain(api):
    assert requests.patch(ME, json={"budget_amount": 80.0}).status_code == 200
    assert _status()["enabled"] is True

    assert requests.patch(ME, json={"clear_budget_amount": True}).status_code == 200

    body = _status()
    assert body["enabled"] is False
    assert body["amount"] is None


def test__patch_me__UnknownBudgetPeriod__IsBusinessRuleViolation(api):
    resp = requests.patch(ME, json={"budget_period": "fortnightly"})

    assert resp.status_code == 422
    assert resp.json()["errors"] == {
        "": [domain_err("Invalid budget period 'fortnightly'.")],
    }


def test__patch_me__MonthlyPeriod__StatusWindowIsCalendarMonth(api):
    assert requests.patch(ME, json={"budget_period": "monthly"}).status_code == 200

    body = _status()

    assert body["period"] == "monthly"
    start = date.fromisoformat(body["period_start"])
    end = date.fromisoformat(body["period_end"])
    assert start.day == 1
    assert end.day == 1
    assert (start.year, start.month) != (end.year, end.month)


#endregion status

#region ---------------- history ----------------


def test__get_budget_history__Default__SixContiguousPeriodsCurrentFirst(api):
    rows = _history()

    assert len(rows) == 6
    assert all(set(r.keys()) == HISTORY_ROW_KEYS for r in rows)
    # Row 0 is the current period — same window /status reports.
    assert rows[0]["period_start"] == _status()["period_start"]
    # Newest-first and gap-free: each older row ends where the newer starts.
    for newer, older in zip(rows, rows[1:]):
        assert older["period_end"] == newer["period_start"]


def test__get_budget_history__SpendInPreviousPeriod__LandsInSecondRow(api):
    baseline_prev = _history()[1]["spent"]
    seeded = seed_purchase(actual_unit_price=9.0)
    previous_mid = datetime.combine(
        date.fromisoformat(_status()["period_start"]) - timedelta(days=3),
        time(12, 0),
    )
    _set_completed_at(seeded["shopping_list_id"], previous_mid)

    rows = _history()

    assert rows[1]["spent"] == round(baseline_prev + 9.0, 2)


def test__get_budget_history__PeriodsOutOfRange__ClampedOrDefaulted(api):
    assert len(_history(periods=0)) == 1
    assert len(_history(periods=100)) == 26
    assert len(_history(periods="lots")) == 6


#endregion history

#region ---------------- auth ----------------


def test__budget_endpoints__AnonymousSession__Unauthorized(api):
    anonymous = requests.Session()

    assert anonymous.get(STATUS).status_code == 401
    assert anonymous.get(HISTORY).status_code == 401


#endregion auth
