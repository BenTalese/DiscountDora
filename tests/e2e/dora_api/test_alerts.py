"""C-9.1 — alerts spine: scoped keys + per-user interaction ledger
(read / snooze / dismiss) + the single server-derived "what counts".

NOTE (2026-06-15): authored static-only — this machine has no Python env, so
the suite was not executed here (see DORA_FOLLOWUPS FU-183). Run on a
provisioned machine before closing C-9.1.
"""
import uuid
from datetime import date, timedelta

import requests

BASE = "http://localhost:5170/api"
PREFS = f"{BASE}/alerts/prefs"
APP_SETTINGS = f"{BASE}/app-settings"
MEAL_PLANS = f"{BASE}/meal-plans"
SHOPPING_LISTS = f"{BASE}/shopping-lists"
RECIPES = f"{BASE}/recipes"


def _any_stock_level_id() -> str:
    levels = requests.get(f"{BASE}/stock-levels").json().get("items") or []
    assert levels, "expected seeded stock levels"
    return levels[0]["stock_level_id"]


def _create_expired_item(name: str) -> None:
    # Past expiry → a high-severity `expired` alert, independent of stock level.
    resp = requests.post(
        f"{BASE}/stock-items",
        json={
            "name": name,
            "stock_level_id": _any_stock_level_id(),
            "expiry_date": "2020-01-01",
        },
    )
    assert resp.status_code in (200, 201), resp.text


def _alerts():
    resp = requests.get(f"{BASE}/alerts")
    assert resp.status_code == 200, resp.text
    return resp.json()


def _find(bucket: list, name: str, kind: str = "expired"):
    return next(
        (a for a in bucket if a["stock_item_name"] == name and a["kind"] == kind),
        None,
    )


def test__alerts__expired_item_surfaces_with_scoped_key(api):
    name = f"alert-spine-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)

    data = _alerts()
    alert = _find(data["items"], name)
    assert alert is not None, "expired item should surface an active alert"
    # Generalised scoped key: stock:<uuid>:<discriminator>
    assert alert["alert_id"].startswith("stock:")
    assert alert["alert_id"].endswith(":expired")
    assert alert["severity"] == "high"
    assert alert["read"] is False
    assert alert["snoozed_until"] is None


def test__alerts__actionable_count_equals_high_plus_medium_in_items(api):
    # The canonical invariant (PROPOSAL_ALERTS §3.4): the badge number
    # equals the count of actionable items actually in the list — no silent
    # low-severity exclusion drift.
    data = _alerts()
    actionable = sum(1 for a in data["items"] if a["severity"] in ("high", "medium"))
    assert data["actionable_count"] == actionable
    assert data["fyi_count"] == sum(1 for a in data["items"] if a["severity"] == "low")
    assert data["snoozed_count"] == len(data["snoozed"])


def test__alerts__snooze_moves_out_of_active_then_clear_restores(api):
    name = f"alert-snooze-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    alert_id = _find(_alerts()["items"], name)["alert_id"]

    snoozed = requests.post(f"{BASE}/alerts/{alert_id}/snooze", json={"days": 7})
    assert snoozed.status_code == 204, snoozed.text

    data = _alerts()
    assert _find(data["items"], name) is None, "snoozed alert should leave the active list"
    moved = _find(data["snoozed"], name)
    assert moved is not None and moved["snoozed_until"] is not None

    cleared = requests.delete(f"{BASE}/alerts/{alert_id}/suppression")
    assert cleared.status_code == 204, cleared.text
    assert _find(_alerts()["items"], name) is not None, "clearing snooze restores the alert"


def test__alerts__mark_read_then_read_all(api):
    name = f"alert-read-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    alert_id = _find(_alerts()["items"], name)["alert_id"]

    read = requests.post(f"{BASE}/alerts/{alert_id}/read")
    assert read.status_code == 204, read.text
    assert _find(_alerts()["items"], name)["read"] is True

    requests.post(f"{BASE}/alerts/{alert_id}/unread")
    assert _find(_alerts()["items"], name)["read"] is False

    assert requests.post(f"{BASE}/alerts/read-all").status_code == 204
    assert _find(_alerts()["items"], name)["read"] is True


def test__alerts__dismiss_hides_everywhere(api):
    name = f"alert-dismiss-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    alert_id = _find(_alerts()["items"], name)["alert_id"]

    assert requests.post(f"{BASE}/alerts/{alert_id}/dismiss").status_code == 204
    data = _alerts()
    assert _find(data["items"], name) is None
    assert _find(data["snoozed"], name) is None


def test__alerts__action_endpoint_accepts_scoped_key(api):
    # The existing act_on_alert must parse the new <scope>:<id>:<kind> key.
    name = f"alert-action-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    alert_id = _find(_alerts()["items"], name)["alert_id"]

    resp = requests.post(f"{BASE}/alerts/{alert_id}/action", json={"action": "reset_expiry"})
    assert resp.status_code == 204, resp.text
    # Expiry cleared → the expired alert no longer fires for this item.
    assert _find(_alerts()["items"], name) is None


def test__alerts__action_endpoint_rejects_non_stock_key(api):
    resp = requests.post(
        f"{BASE}/alerts/meal:no_planned_meals:2026-W25/action",
        json={"action": "reset_expiry"},
    )
    assert resp.status_code == 400, resp.text


# ─────────────────────────────────────────────────────────────────────────
# C-9.2 — per-user preferences (enable/disable + tier override) + configurable
# household thresholds. The count split always equals the per-alert effective
# `tier`; tests clean up after themselves (prefs are per-user + persistent, and
# the threshold is household-wide — no per-test DB isolation yet, FU-169).
# ─────────────────────────────────────────────────────────────────────────
ALL_KINDS = (
    "expired", "expiring_soon", "out_of_stock",
    "low_stock", "essential_low", "stocktake_overdue",
)


def _prefs() -> dict:
    resp = requests.get(PREFS)
    assert resp.status_code == 200, resp.text
    return {p["kind"]: p for p in resp.json()["prefs"]}


def _reset_pref(kind: str) -> None:
    requests.patch(PREFS, json={"kind": kind, "enabled": True, "tier_override": None})


def _assert_count_split_matches_tiers(data: dict) -> None:
    # The canonical C-9.2 invariant: the badge/FYI counts are exactly the
    # per-alert effective-tier tallies — no drift between count and list.
    assert data["actionable_count"] == sum(1 for a in data["items"] if a["tier"] == "actionable")
    assert data["fyi_count"] == sum(1 for a in data["items"] if a["tier"] == "fyi")


def test__alert_prefs__defaults_expose_every_kind_with_sensible_tiers(api):
    prefs = _prefs()
    for kind in ALL_KINDS:
        assert kind in prefs, f"{kind} missing from prefs"
        assert prefs[kind]["enabled"] is True
        assert prefs[kind]["tier_override"] is None
    # PROPOSAL_ALERTS §5 default tiers.
    assert prefs["expired"]["default_tier"] == "actionable"
    assert prefs["out_of_stock"]["default_tier"] == "actionable"
    assert prefs["low_stock"]["default_tier"] == "fyi"
    assert prefs["stocktake_overdue"]["default_tier"] == "fyi"
    assert prefs["expired"]["effective_tier"] == "actionable"


def test__alert_prefs__disabling_a_kind_removes_it_from_list_and_counts(api):
    name = f"alert-pref-disable-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    assert _find(_alerts()["items"], name) is not None
    try:
        assert requests.patch(PREFS, json={"kind": "expired", "enabled": False}).status_code == 200
        after = _alerts()
        assert all(a["kind"] != "expired" for a in after["items"]), "disabled kind leaves active list"
        assert all(a["kind"] != "expired" for a in after["snoozed"]), "disabled kind leaves snoozed list"
        _assert_count_split_matches_tiers(after)
    finally:
        _reset_pref("expired")
    assert _find(_alerts()["items"], name) is not None, "re-enabling restores the alert"


def test__alert_prefs__tier_override_moves_kind_between_actionable_and_fyi(api):
    name = f"alert-pref-tier-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    active = _find(_alerts()["items"], name)
    assert active is not None and active["tier"] == "actionable"  # default for expired
    try:
        assert requests.patch(PREFS, json={"kind": "expired", "tier_override": "fyi"}).status_code == 200
        after = _alerts()
        moved = _find(after["items"], name)
        assert moved is not None and moved["tier"] == "fyi", "override moves the kind to FYI"
        _assert_count_split_matches_tiers(after)
    finally:
        _reset_pref("expired")
    restored = _find(_alerts()["items"], name)
    assert restored is not None and restored["tier"] == "actionable", "clearing the override restores the default"


def test__alert_prefs__rejects_unknown_kind_and_invalid_tier(api):
    # R-010 — validate the vocabulary on write.
    assert requests.patch(PREFS, json={"kind": "not_a_kind", "enabled": False}).status_code == 400
    assert requests.patch(PREFS, json={"kind": "expired", "tier_override": "bogus"}).status_code == 400
    try:
        assert requests.patch(PREFS, json={"kind": "expired", "tier_override": "actionable"}).status_code == 200
    finally:
        _reset_pref("expired")


def test__alerts__expiring_soon_window_threshold_re_derives(api):
    # A 5-day-out item is "expiring soon" under the default 7-day window, but
    # not under a 3-day window — the evaluator must read the household setting.
    name = f"alert-window-{uuid.uuid4().hex[:8]}"
    resp = requests.post(f"{BASE}/stock-items", json={
        "name": name,
        "stock_level_id": _any_stock_level_id(),
        "expiry_date": (date.today() + timedelta(days=5)).isoformat(),
    })
    assert resp.status_code in (200, 201), resp.text
    assert _find(_alerts()["items"], name, kind="expiring_soon") is not None

    original = requests.get(APP_SETTINGS).json()["expiring_soon_window_days"]
    try:
        patched = requests.patch(APP_SETTINGS, json={"expiring_soon_window_days": 3})
        assert patched.status_code == 200, patched.text
        assert patched.json()["expiring_soon_window_days"] == 3
        assert _find(_alerts()["items"], name, kind="expiring_soon") is None, \
            "a 5-day-out item is not expiring soon under a 3-day window"
    finally:
        assert requests.patch(APP_SETTINGS, json={"expiring_soon_window_days": original}).status_code == 200
    assert _find(_alerts()["items"], name, kind="expiring_soon") is not None, "restored window re-fires the alert"


def test__alerts__history_lists_dismissed_with_resolved_label(api):
    # C-9.3 — alerts are derived, so "history" is the ledger of decisions; a
    # dismissed alert surfaces in /history with its stock name resolved.
    name = f"alert-history-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    alert_id = _find(_alerts()["items"], name)["alert_id"]
    assert requests.post(f"{BASE}/alerts/{alert_id}/dismiss").status_code == 204

    resp = requests.get(f"{BASE}/alerts/history")
    assert resp.status_code == 200, resp.text
    entry = next((e for e in resp.json()["entries"] if e["alert_key"] == alert_id), None)
    assert entry is not None, "a dismissed alert should appear in history"
    assert entry["state"] == "dismissed"
    assert entry["label"] == name, "stock item name resolved from the alert key"
    assert entry["kind"] == "expired"


# ─────────────────────────────────────────────────────────────────────────
# C-9.4 — forward-looking nudges: `no_planned_meals` (next week empty) and
# `shopping_day` (a list's planned shop date is near). Both are non-stock kinds:
# they carry no stock_item_id and deep-link via kind (+ target_id for the list).
# ─────────────────────────────────────────────────────────────────────────
def _find_kind(data: dict, kind: str, target_id: str | None = None):
    return next(
        (
            a for a in data["items"]
            if a["kind"] == kind and (target_id is None or a.get("target_id") == target_id)
        ),
        None,
    )


def _household_today() -> date:
    return date.fromisoformat(requests.get(f"{MEAL_PLANS}/today").json()["today"])


def test__alerts__no_planned_meals_fires_when_next_week_empty_and_clears(api):
    # The seed plans only THIS week, so next week starts empty → the nudge fires.
    assert _find_kind(_alerts(), "no_planned_meals") is not None, \
        "an empty next week should surface the no-planned-meals nudge"

    today = _household_today()
    next_monday = today + timedelta(days=7 - today.weekday())
    recipe_id = requests.get(f"{RECIPES}?limit=1").json()["items"][0]["recipe_id"]
    created = requests.post(MEAL_PLANS, json={
        "start_date": next_monday.isoformat(),
        "entries": [{
            "recipe_id": recipe_id,
            "scheduled_for": next_monday.isoformat(),
            "servings": 2,
            "slot": "Dinner",
        }],
    })
    assert created.status_code in (200, 201), created.text
    plan_id = created.json()["meal_plan_id"]
    try:
        assert _find_kind(_alerts(), "no_planned_meals") is None, \
            "planning a meal next week clears the nudge"
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")
    # Removing the only next-week plan empties it again → the nudge re-fires.
    assert _find_kind(_alerts(), "no_planned_meals") is not None, \
        "deleting the plan re-empties next week and re-fires the nudge"


def test__alerts__no_planned_meals_is_fyi_and_carries_no_stock_item(api):
    alert = _find_kind(_alerts(), "no_planned_meals")
    assert alert is not None
    assert alert["alert_id"].startswith("meal:no_planned_meals:")
    assert alert["tier"] == "fyi"
    assert alert["stock_item_id"] is None
    assert alert["target_id"] is None


def test__alerts__shopping_day_fires_within_window_and_clears_when_done(api):
    today = _household_today()
    created = requests.post(SHOPPING_LISTS, json={
        "name": f"shopping-day-{uuid.uuid4().hex[:8]}",
        "planned_shop_date": (today + timedelta(days=2)).isoformat(),
    })
    assert created.status_code == 201, created.text
    list_id = created.json()["shopping_list_id"]
    try:
        alert = _find_kind(_alerts(), "shopping_day", target_id=list_id)
        assert alert is not None, "a list two days out should surface a shopping-day nudge"
        assert alert["alert_id"] == f"list:{list_id}:shopping_day"
        assert alert["tier"] == "fyi"
        assert alert["stock_item_id"] is None

        # Finishing the list (→ done) clears the nudge.
        assert requests.post(f"{SHOPPING_LISTS}/{list_id}/start").status_code == 204
        assert requests.post(f"{SHOPPING_LISTS}/{list_id}/finish").status_code == 200
        assert _find_kind(_alerts(), "shopping_day", target_id=list_id) is None, \
            "a done list no longer nudges"
    finally:
        requests.delete(f"{SHOPPING_LISTS}/{list_id}")


def test__alerts__shopping_day_silent_outside_window(api):
    # A planned date well beyond the window must not nudge.
    today = _household_today()
    created = requests.post(SHOPPING_LISTS, json={
        "name": f"shopping-day-far-{uuid.uuid4().hex[:8]}",
        "planned_shop_date": (today + timedelta(days=30)).isoformat(),
    })
    assert created.status_code == 201, created.text
    list_id = created.json()["shopping_list_id"]
    try:
        assert _find_kind(_alerts(), "shopping_day", target_id=list_id) is None, \
            "a list 30 days out is outside the shopping-day window"
    finally:
        requests.delete(f"{SHOPPING_LISTS}/{list_id}")


def test__alerts__shopping_day_overdue_fires_and_escalates_severity(api):
    # FU-074 — a not-yet-done list whose planned shop date has already
    # passed should keep nudging (mirrors the in-page banner's overdue
    # state). Severity bumps from low → medium so it sorts above plain
    # upcoming nudges; tier stays FYI (the kind default).
    today = _household_today()
    created = requests.post(SHOPPING_LISTS, json={
        "name": f"shopping-day-overdue-{uuid.uuid4().hex[:8]}",
        "planned_shop_date": (today - timedelta(days=2)).isoformat(),
    })
    assert created.status_code == 201, created.text
    list_id = created.json()["shopping_list_id"]
    try:
        alert = _find_kind(_alerts(), "shopping_day", target_id=list_id)
        assert alert is not None, "an overdue shop day should still nudge"
        assert alert["alert_id"] == f"list:{list_id}:shopping_day"
        assert alert["tier"] == "fyi"
        assert alert["severity"] == "medium", \
            "overdue bumps the severity from low to medium so it sorts above upcoming"
        assert "2 days ago" in alert["message"], alert["message"]

        # Finishing the list clears it (same close condition as the
        # upcoming case — only status, not the date passing).
        assert requests.post(f"{SHOPPING_LISTS}/{list_id}/start").status_code == 204
        assert requests.post(f"{SHOPPING_LISTS}/{list_id}/finish").status_code == 200
        assert _find_kind(_alerts(), "shopping_day", target_id=list_id) is None, \
            "an overdue list still clears the nudge once it's marked done"
    finally:
        requests.delete(f"{SHOPPING_LISTS}/{list_id}")


def test__alert_prefs__exposes_the_new_c94_kinds_as_fyi(api):
    prefs = _prefs()
    for kind in ("no_planned_meals", "shopping_day"):
        assert kind in prefs, f"{kind} missing from prefs"
        assert prefs[kind]["enabled"] is True
        assert prefs[kind]["default_tier"] == "fyi"


# ── C-9.6 — Upcoming "this fortnight" timeline (server-owned aggregation) ──

UPCOMING = f"{BASE}/alerts/upcoming"


def _upcoming(days: int | None = None) -> dict:
    url = UPCOMING + (f"?days={days}" if days is not None else "")
    resp = requests.get(url)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _upcoming_day(data: dict, iso: str):
    return next((d for d in data["dates"] if d["date"] == iso), None)


def test__upcoming__window_is_household_today_for_n_days(api):
    today = _household_today()
    data = _upcoming()  # default 14-day window
    assert data["start"] == today.isoformat()
    assert data["days"] == 14
    assert data["end"] == (today + timedelta(days=13)).isoformat()


def test__upcoming__shopping_and_meal_land_on_their_dates(api):
    today = _household_today()
    shop_date = today + timedelta(days=2)
    created = requests.post(SHOPPING_LISTS, json={
        "name": f"upcoming-shop-{uuid.uuid4().hex[:8]}",
        "planned_shop_date": shop_date.isoformat(),
    })
    assert created.status_code == 201, created.text
    list_id = created.json()["shopping_list_id"]

    # A meal next week (within the 14-day window) — its date is empty in the
    # seed, so the assertion is deterministic.
    meal_date = today + timedelta(days=7 - today.weekday())
    recipe_id = requests.get(f"{RECIPES}?limit=1").json()["items"][0]["recipe_id"]
    plan = requests.post(MEAL_PLANS, json={
        "start_date": meal_date.isoformat(),
        "entries": [{
            "recipe_id": recipe_id,
            "scheduled_for": meal_date.isoformat(),
            "servings": 2,
            "slot": "Dinner",
        }],
    })
    assert plan.status_code in (200, 201), plan.text
    plan_id = plan.json()["meal_plan_id"]
    try:
        data = _upcoming()
        shop_day = _upcoming_day(data, shop_date.isoformat())
        assert shop_day is not None, "the planned shop date should appear in the window"
        assert any(s["list_id"] == list_id for s in shop_day["shopping"]), \
            "the created list should be aggregated under its planned shop date"

        meal_day = _upcoming_day(data, meal_date.isoformat())
        assert meal_day is not None, "the planned meal date should appear in the window"
        assert any(m["recipe_id"] == recipe_id for m in meal_day["meals"]), \
            "the planned meal should be aggregated under its scheduled date"
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")
        requests.delete(f"{SHOPPING_LISTS}/{list_id}")


def test__upcoming__expiry_lands_on_its_date(api):
    today = _household_today()
    expiry = today + timedelta(days=1)
    created = requests.post(f"{BASE}/stock-items", json={
        "name": f"upcoming-expiry-{uuid.uuid4().hex[:8]}",
        "stock_level_id": _any_stock_level_id(),
        "expiry_date": expiry.isoformat(),
    })
    assert created.status_code in (200, 201), created.text
    item_id = created.json()["stock_item_id"]
    try:
        day = _upcoming_day(_upcoming(), expiry.isoformat())
        assert day is not None, "the expiry date should appear in the window"
        assert any(e["stock_item_id"] == item_id for e in day["expiries"]), \
            "the expiring item should be aggregated under its expiry date"
    finally:
        requests.delete(f"{BASE}/stock-items/{item_id}")


def test__upcoming__respects_the_window_bound(api):
    # A shop date beyond the default window is excluded, but visible once the
    # window is widened to include it — proving the bound is honoured, not cosmetic.
    today = _household_today()
    far_date = today + timedelta(days=20)
    created = requests.post(SHOPPING_LISTS, json={
        "name": f"upcoming-far-{uuid.uuid4().hex[:8]}",
        "planned_shop_date": far_date.isoformat(),
    })
    assert created.status_code == 201, created.text
    list_id = created.json()["shopping_list_id"]
    try:
        assert _upcoming_day(_upcoming(), far_date.isoformat()) is None, \
            "a date 20 days out is outside the default 14-day window"
        wide = _upcoming(days=25)
        day = _upcoming_day(wide, far_date.isoformat())
        assert day is not None and any(s["list_id"] == list_id for s in day["shopping"]), \
            "widening the window to 25 days should surface the far list"
    finally:
        requests.delete(f"{SHOPPING_LISTS}/{list_id}")


def test__upcoming__clamps_excessive_days(api):
    # The window is clamped to a sane max so a caller can't request an
    # unbounded scan (R-003 — one bound, server-side).
    assert _upcoming(days=9999)["days"] == 31
