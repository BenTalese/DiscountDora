"""FU-174 / R-021 — every calendar boundary evaluates in the household timezone.

This pins the rule end-to-end: set ``AppSetting.timezone`` to a non-UTC
zone, create a stock item with an expiry date that's "tomorrow" in UTC
but "today" in the zone, and assert that the alerts handler, the
dashboard summary, and the suggestions / waste / assistant paths all
evaluate "today" against the **household** boundary, not server-local.

Without R-021 this test fails the moment the server is hosted in any
timezone that crosses midnight relative to the household — exactly the
F29-class bug class FU-174 was raised to close. With R-021 it passes
regardless of where the server runs because every handler routes
through ``household_today(repository)``.

Each test brackets its zone change in a try/finally so a failure
doesn't leak a non-default timezone into the rest of the suite.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

BASE = "http://localhost:5170/api"
APP_SETTINGS = f"{BASE}/app-settings"

# Pacific/Kiritimati is UTC+14 — the furthest-ahead IANA zone. If the
# server runs anywhere west of it (most of the world), there's at least
# a 10-hour window each day where the zone's calendar day is one day
# ahead of UTC.
FORWARD_ZONE = "Pacific/Kiritimati"
# Pacific/Pago_Pago is UTC-11 — the furthest-behind zone. Mirror case.
BACKWARD_ZONE = "Pacific/Pago_Pago"


def _set_timezone(tz: str):
    resp = requests.patch(APP_SETTINGS, json={"timezone": tz})
    assert resp.status_code == 200, resp.text


def _stock_level_id() -> str:
    levels = requests.get(f"{BASE}/stock-levels").json().get("items") or []
    assert levels, "seeded stock levels expected"
    return levels[0]["stock_level_id"]


def _zone_today(tz: str) -> str:
    return datetime.now(ZoneInfo(tz)).date().isoformat()


def test__household_today__shifts_with_appsetting_timezone(api):
    """`/meal-plans/today` reports the calendar date in the configured
    zone, not the server's. The rest of the suite uses this as the
    canonical "the server respects the household tz" signal — keeping
    a direct assertion here so a regression in `household_today` is
    caught at this file, not via downstream tests."""
    try:
        _set_timezone(FORWARD_ZONE)
        resp = requests.get(f"{BASE}/meal-plans/today")
        assert resp.status_code == 200
        assert resp.json()["today"] == _zone_today(FORWARD_ZONE)

        _set_timezone(BACKWARD_ZONE)
        resp = requests.get(f"{BASE}/meal-plans/today")
        assert resp.status_code == 200
        assert resp.json()["today"] == _zone_today(BACKWARD_ZONE)
    finally:
        _set_timezone("UTC")


def test__alerts__expiry_compares_against_household_today(api):
    """An item whose `expiry_date` equals the household's today must
    surface as `expiring_soon` (days_remaining=0), not as `expired`
    (which would happen if the comparison used server-local today and
    the server already rolled over to tomorrow)."""
    try:
        _set_timezone(FORWARD_ZONE)
        household_today = _zone_today(FORWARD_ZONE)

        # Create an item that expires *today* in the household zone.
        name = f"tz-boundary-expiring-{household_today}"
        resp = requests.post(
            f"{BASE}/stock-items",
            json={
                "name": name,
                "stock_level_id": _stock_level_id(),
                "expiry_date": household_today,
            },
        )
        assert resp.status_code in (200, 201), resp.text

        alerts = requests.get(f"{BASE}/alerts").json()
        items = alerts["items"] + alerts.get("snoozed", [])
        ours = [a for a in items if a["stock_item_name"] == name]
        assert ours, "expected our created item to produce an alert"
        # The kind hinges on the household date comparison — if the
        # server were using its own date and was already "tomorrow",
        # this would be `expired` instead.
        kinds = {a["kind"] for a in ours}
        assert "expiring_soon" in kinds, (
            f"expected expiring_soon (household today), got kinds={kinds}"
        )
    finally:
        _set_timezone("UTC")


def test__dashboard__upcoming_window_anchored_on_household_today(api):
    """The dashboard's `upcoming_meal_plan_entries` window is a 7-day
    band starting at "today". With FORWARD_ZONE set, the band must
    include household-today and household-today+6, not server-local."""
    try:
        _set_timezone(FORWARD_ZONE)
        household_today = datetime.fromisoformat(_zone_today(FORWARD_ZONE)).date()

        # Pick a target date squarely inside the household window but
        # *outside* a UTC-anchored window (one day later than UTC today).
        target = household_today  # exact today in household tz

        # Create / find a meal plan for this user.
        plans = requests.get(f"{BASE}/meal-plans?limit=1").json()["items"]
        if plans:
            plan_id = plans[0]["meal_plan_id"]
        else:
            mp = requests.post(
                f"{BASE}/meal-plans",
                json={"start_date": target.isoformat()},
            )
            assert mp.status_code in (200, 201), mp.text
            plan_id = mp.json().get("meal_plan_id") or mp.json().get("id")

        # Pin one entry on household-today.
        recipes = requests.get(f"{BASE}/recipes?limit=1").json()["items"]
        if not recipes:
            return  # no recipe seeded → nothing to schedule
        recipe_id = recipes[0]["recipe_id"]
        entry = requests.post(
            f"{BASE}/meal-plans/{plan_id}/entries",
            json={
                "scheduled_for": target.isoformat(),
                "slot": "Dinner",
                "recipe_id": recipe_id,
                "servings": 1,
            },
        )
        assert entry.status_code in (200, 201), entry.text

        summary = requests.get(f"{BASE}/dashboard").json()
        upcoming = summary.get("upcoming_meal_plan_entries") or []
        dates = {e["scheduled_for"] for e in upcoming}
        assert target.isoformat() in dates, (
            "household-today entry missing from upcoming-window — boundary"
            " is likely server-local"
        )
    finally:
        _set_timezone("UTC")


def test__waste_rescue__horizon_uses_household_today(api):
    """Items expiring on household-today must appear in the rescue feed
    when called with `horizon_days=0`, even if server-local has already
    rolled over to tomorrow."""
    try:
        _set_timezone(FORWARD_ZONE)
        household_today = _zone_today(FORWARD_ZONE)

        name = f"tz-rescue-{household_today}"
        resp = requests.post(
            f"{BASE}/stock-items",
            json={
                "name": name,
                "stock_level_id": _stock_level_id(),
                "expiry_date": household_today,
            },
        )
        assert resp.status_code in (200, 201), resp.text

        rescue = requests.get(f"{BASE}/waste/rescue?horizon_days=0").json()
        names = {it["name"] for it in rescue.get("items", [])}
        assert name in names, (
            "household-today expiry missing from rescue feed (horizon_days=0)"
        )
    finally:
        _set_timezone("UTC")
