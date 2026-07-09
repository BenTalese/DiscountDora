"""FU-317 Chunk 4 — `meal_reconcile_overdue` alert kind + the
`reconcile_meals_pending` suggestion kind.

Both surfaces fire off the same signal
(`reconcile.reconcile_overdue_signal`, R-003) so the threshold check
below covers both: below threshold → neither surfaces; above threshold →
both surface, with matching count / days-back.

Threshold (D1, locked by impl-plan):
  * unresolved_count ≥ 3
  * oldest_days_back ≥ 4
"""
from datetime import date, timedelta

import requests
from sqlalchemy import text

from dora_api.app import db

BASE = "http://localhost:5170/api"
MEAL_PLANS = f"{BASE}/meal-plans"
APP_SETTINGS = f"{BASE}/app-settings"
RECIPES = f"{BASE}/recipes"


def _household_today() -> date:
    return date.fromisoformat(requests.get(f"{MEAL_PLANS}/today").json()["today"])


def _trigger_sweep() -> None:
    resp = requests.get(f"{MEAL_PLANS}/today")
    assert resp.status_code == 200, resp.text


def _pick_recipe_id() -> str:
    items = requests.get(f"{RECIPES}?limit=1").json()["items"]
    assert items, "seed expected to have a recipe"
    return items[0]["recipe_id"]


def _bump_pool_to(recipe_id: str, target: int) -> None:
    resp = requests.get(f"{RECIPES}/{recipe_id}")
    current = int(resp.json()["available_meals"])
    delta = target - current
    if delta > 0:
        requests.post(f"{RECIPES}/{recipe_id}/cook", json={"meals_cooked": delta})


def _create_past_day_entry(recipe_id: str, days_ago: int) -> tuple[str, str]:
    scheduled = _household_today() - timedelta(days=days_ago)
    created = requests.post(MEAL_PLANS, json={
        "start_date": scheduled.isoformat(),
        "entries": [{
            "recipe_id": recipe_id,
            "scheduled_for": scheduled.isoformat(),
            "servings": 1,
            "slot": "Dinner",
        }],
    })
    assert created.status_code in (200, 201), created.text
    body = created.json()
    return body["meal_plan_id"], body["entries"][0]["entry_id"]


def _clear_test_receipts_and_plans() -> None:
    """Best-effort cleanup — the sweep never re-fires on already-processed
    entries, but plans/entries from previous tests could still contribute
    to the signal. Called at the top of each test."""
    with db.engine.begin() as conn:
        conn.execute(text('DELETE FROM "MealPlanReconcileReceipt"'))


def _find_alert(kind: str):
    data = requests.get(f"{BASE}/alerts").json()
    for a in data["items"] + data.get("snoozed", []):
        if a["kind"] == kind:
            return a
    return None


def _find_suggestion(kind: str):
    data = requests.get(f"{BASE}/suggestions").json()
    for s in data.get("items", data if isinstance(data, list) else []):
        if isinstance(s, dict) and s.get("kind") == kind:
            return s
    return None


# ── Below-threshold: neither surface fires ──────────────────────────────

def test__below_threshold_count__neither_alert_nor_suggestion_fires(api):
    """Two unresolved entries — count < 3 → no fire, either surface."""
    _clear_test_receipts_and_plans()
    recipe_id = _pick_recipe_id()
    _bump_pool_to(recipe_id, target=10)
    plan_ids = []
    try:
        for i in range(2):
            plan_id, _ = _create_past_day_entry(recipe_id, days_ago=5)
            plan_ids.append(plan_id)
        _trigger_sweep()

        assert _find_alert("meal_reconcile_overdue") is None
        assert _find_suggestion("reconcile_meals_pending") is None
    finally:
        for pid in plan_ids:
            requests.delete(f"{MEAL_PLANS}/{pid}")


def test__above_count_but_all_recent__neither_surface_fires(api):
    """Four unresolved entries but ALL scheduled 2 days ago (< 4 days-back
    threshold) → no fire."""
    _clear_test_receipts_and_plans()
    recipe_id = _pick_recipe_id()
    _bump_pool_to(recipe_id, target=10)
    plan_ids = []
    try:
        for _ in range(4):
            plan_id, _ = _create_past_day_entry(recipe_id, days_ago=2)
            plan_ids.append(plan_id)
        _trigger_sweep()

        assert _find_alert("meal_reconcile_overdue") is None
        assert _find_suggestion("reconcile_meals_pending") is None
    finally:
        for pid in plan_ids:
            requests.delete(f"{MEAL_PLANS}/{pid}")


# ── At-threshold: both surfaces fire, matching payload ──────────────────

def test__above_threshold__both_alert_and_suggestion_fire(api):
    """Three unresolved entries with oldest 5 days back → both fire.
    The `alert_id` scope is `meal:...`, and the suggestion payload
    carries the same counts."""
    _clear_test_receipts_and_plans()
    recipe_id = _pick_recipe_id()
    _bump_pool_to(recipe_id, target=10)
    plan_ids = []
    try:
        for days_ago in (5, 4, 4):
            plan_id, _ = _create_past_day_entry(recipe_id, days_ago=days_ago)
            plan_ids.append(plan_id)
        _trigger_sweep()

        alert = _find_alert("meal_reconcile_overdue")
        assert alert is not None, "alert should fire at threshold"
        assert alert["alert_id"].startswith("meal:meal_reconcile_overdue:")
        assert alert["severity"] == "low"
        assert "3" in alert["message"] or "past meals" in alert["message"]

        suggestion = _find_suggestion("reconcile_meals_pending")
        assert suggestion is not None, "suggestion should fire at threshold"
        assert suggestion["payload"]["unresolved_count"] == 3
        assert suggestion["payload"]["oldest_days_back"] >= 4
        # Deep-link points at the reconcile page (Chunk 5 will register it).
        assert suggestion["primary_action"]["path"] == "/meal-plans/reconcile"
    finally:
        for pid in plan_ids:
            requests.delete(f"{MEAL_PLANS}/{pid}")


# ── Alert kind registered with sensible default ─────────────────────────

def test__alert_prefs__meal_reconcile_overdue_listed_as_fyi_by_default(api):
    """The alerts-prefs endpoint should list the new kind with the FYI
    default tier — matches `no_planned_meals` / `shopping_day` (both
    forward/backward-looking nudges)."""
    resp = requests.get(f"{BASE}/alerts/prefs")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    kinds = {p["kind"]: p for p in body.get("items", body if isinstance(body, list) else [])}
    assert "meal_reconcile_overdue" in kinds, kinds
    assert kinds["meal_reconcile_overdue"]["tier"] == "fyi"


# ── Firing → clearing round-trip ────────────────────────────────────────

def test__resolving_all_queue_entries_clears_both_surfaces(api):
    """After the threshold fires, resolving every entry (verb `cooked`)
    should clear the queue → neither surface fires."""
    _clear_test_receipts_and_plans()
    recipe_id = _pick_recipe_id()
    _bump_pool_to(recipe_id, target=10)
    plan_ids: list[str] = []
    entry_ids: list[str] = []
    try:
        for days_ago in (5, 5, 5):
            pid, eid = _create_past_day_entry(recipe_id, days_ago=days_ago)
            plan_ids.append(pid)
            entry_ids.append(eid)
        _trigger_sweep()
        assert _find_alert("meal_reconcile_overdue") is not None

        for eid in entry_ids:
            r = requests.post(f"{MEAL_PLANS}/reconcile/{eid}", json={"verb": "cooked"})
            assert r.status_code == 200, r.text

        assert _find_alert("meal_reconcile_overdue") is None
        assert _find_suggestion("reconcile_meals_pending") is None
    finally:
        for pid in plan_ids:
            requests.delete(f"{MEAL_PLANS}/{pid}")
