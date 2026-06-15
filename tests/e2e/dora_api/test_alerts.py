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
