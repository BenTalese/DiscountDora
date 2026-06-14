"""Meal Plans C-2.K — household-timezone "today" boundary.

Covers:
  * GET /api/meal-plans/today returns the current date in the household
    timezone (defaults to UTC).
  * AppSetting.timezone round-trips (PATCH /app-settings → GET reflects it),
    and a far-offset zone shifts what /today reports — proving the boundary
    is evaluated in the configured zone, not server-local.
  * An invalid IANA zone is rejected with a 400 and leaves the stored value
    unchanged.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

MEAL_PLANS = "http://localhost:5170/api/meal-plans"
APP_SETTINGS = "http://localhost:5170/api/app-settings"


def _today() -> str:
    resp = requests.get(f"{MEAL_PLANS}/today")
    assert resp.status_code == 200, resp.text
    return resp.json()["today"]


def _set_timezone(tz: str):
    return requests.patch(APP_SETTINGS, json={"timezone": tz})


def test_today_endpoint_returns_the_household_date():
    # Fresh install defaults to UTC, so /today equals the UTC calendar date.
    assert _today() == datetime.now(ZoneInfo("UTC")).date().isoformat()


def test_timezone_round_trips_and_shifts_today():
    try:
        resp = _set_timezone("Pacific/Kiritimati")  # UTC+14, furthest ahead
        assert resp.status_code == 200, resp.text
        assert resp.json()["timezone"] == "Pacific/Kiritimati"

        got = requests.get(APP_SETTINGS)
        assert got.status_code == 200, got.text
        assert got.json()["timezone"] == "Pacific/Kiritimati"

        # /today is computed in the configured zone, not server-local.
        assert _today() == datetime.now(ZoneInfo("Pacific/Kiritimati")).date().isoformat()
    finally:
        assert _set_timezone("UTC").status_code == 200


def test_invalid_timezone_is_rejected():
    resp = _set_timezone("Not/ARealZone")
    assert resp.status_code == 400, resp.text
    # The bogus value was never stored.
    assert requests.get(APP_SETTINGS).json()["timezone"] != "Not/ARealZone"
