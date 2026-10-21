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

from dora_api.app import app, db

BASE = "http://localhost:5170/api"
MEAL_PLANS = f"{BASE}/meal-plans"
APP_SETTINGS = f"{BASE}/app-settings"
RECIPES = f"{BASE}/recipes"


def _household_today() -> date:
    return date.fromisoformat(requests.get(f"{MEAL_PLANS}/today").json()["today"])


def _trigger_sweep() -> None:
    resp = requests.get(f"{MEAL_PLANS}/today")
    assert resp.status_code == 200, resp.text


def _set_auto_drain(value: bool) -> None:
    resp = requests.patch(APP_SETTINGS, json={"auto_drain_past_meals": value})
    assert resp.status_code == 200, resp.text


# The overdue nudge is a MANUAL-mode concept (owner 2026-08-13): in auto mode
# `unresolved_auto` entries aren't pending, so the signal is intentionally
# suppressed (covered by `test__auto_mode_suppresses_the_overdue_nudge`). Every
# firing test below therefore pins manual mode so the sweep leaves genuinely
# pending `unresolved_manual` entries for the threshold logic to act on.


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
    """See test_reconcile_verbs.py for the design note. TL;DR: the create
    endpoint refuses past `scheduled_for`, so we post today and backdate
    via SQL to seed something the sweep will pick up."""
    from tests.support import uuid_bind
    today = _household_today()
    past = today - timedelta(days=days_ago)
    created = requests.post(MEAL_PLANS, json={
        "start_date": today.isoformat(),
        "entries": [{
            "recipe_id": recipe_id,
            "scheduled_for": today.isoformat(),
            "servings": 1,
            "slot": "Dinner",
        }],
    })
    assert created.status_code in (200, 201), created.text
    body = created.json()
    plan_id = body["meal_plan_id"]
    entry_id = body["entries"][0]["meal_plan_entry_id"]
    with app.app_context(), db.engine.begin() as conn:
        conn.execute(
            text('UPDATE "MealPlanEntry" SET scheduled_for = :past WHERE id = :eid'),
            {"past": past.isoformat(), "eid": uuid_bind(entry_id)},
        )
        conn.execute(
            text('UPDATE "MealPlan" SET start_date = :past WHERE id = :pid'),
            {"past": past.isoformat(), "pid": uuid_bind(plan_id)},
        )
    return plan_id, entry_id


def _clear_test_receipts_and_plans() -> None:
    """Best-effort cleanup — the signal counts *unresolved past-day entries*,
    so any residue from previous test runs (leftover MealPlanEntry rows
    whose containing plan wasn't cleanly torn down) inflates the count.
    Called at the top of each test.

    Order matters: children (receipts, past-day entries) before parents.
    The `scheduled_for < today` guard preserves any seeded future entries
    that live outside the reconcile signal's window.
    """
    today = _household_today()
    with app.app_context(), db.engine.begin() as conn:
        conn.execute(text('DELETE FROM "MealPlanReconcileReceipt"'))
        conn.execute(
            text('DELETE FROM "MealPlanEntry" WHERE scheduled_for < :today'),
            {"today": today.isoformat()},
        )
        conn.execute(
            text(
                'DELETE FROM "MealPlan" WHERE NOT EXISTS ('
                '  SELECT 1 FROM "MealPlanEntry" mpe '
                '  WHERE mpe.meal_plan_id = "MealPlan".id'
                ')'
            )
        )


def _find_alert(kind: str):
    data = requests.get(f"{BASE}/alerts").json()
    for a in data["items"] + data.get("snoozed", []):
        if a["kind"] == kind:
            return a
    return None


def _find_suggestion(kind: str):
    data = requests.get(f"{BASE}/suggestions").json()
    for s in data.get("suggestions", []):
        if isinstance(s, dict) and s.get("kind") == kind:
            return s
    return None


# ── Below-threshold: neither surface fires ──────────────────────────────

def test__below_threshold_count__neither_alert_nor_suggestion_fires(api):
    """Two unresolved entries — count < 3 → no fire, either surface."""
    _clear_test_receipts_and_plans()
    _set_auto_drain(False)
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
    _set_auto_drain(False)
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
    _set_auto_drain(False)
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

        # The suggestion generator + payload go through the direct handler.
        # The `/api/suggestions` endpoint caps the response at 8 sorted by
        # severity DESC; in a session-shared DB the seeded state produces
        # plenty of higher-severity suggestions that can crowd this LOW-
        # severity nudge out of the top slice. That's a legitimate ranking
        # concern for the UI, not a signal-correctness concern (the alert
        # already proved the shared signal fired). So we bypass the ranker
        # here and hit the generator directly to verify its payload.
        from dora_api.features.suggestions.generators import \
            generate_reconcile_meals_pending
        from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
        with app.app_context():
            produced = generate_reconcile_meals_pending(
                SqlAlchemyRepository(), user_id=None,
            )
        assert produced, "suggestion generator should fire at threshold"
        payload = produced[0].payload
        assert payload["unresolved_count"] == 3
        assert payload["oldest_days_back"] >= 4
        # Deep-link points at the reconcile page.
        assert produced[0].primary_action["path"] == "/meal-plans/reconcile"
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
    kinds = {p["kind"]: p for p in body.get("prefs", [])}
    assert "meal_reconcile_overdue" in kinds, kinds
    assert kinds["meal_reconcile_overdue"]["tier"] == "fyi"


# ── Firing → clearing round-trip ────────────────────────────────────────

def test__resolving_all_queue_entries_clears_both_surfaces(api):
    """After the threshold fires, resolving every entry (verb `cooked`)
    should clear the queue → neither surface fires."""
    _clear_test_receipts_and_plans()
    _set_auto_drain(False)
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


# ── Auto mode suppresses the nudge (owner 2026-08-13) ───────────────────

def test__auto_mode_suppresses_the_overdue_nudge(api):
    """In auto-drain mode Dora handles past meals silently, so even a queue
    that WOULD trip the threshold in manual mode (3 entries, oldest 5 days
    back) fires neither the alert nor the suggestion — the auto-drained
    entries aren't 'pending'. They live in the read-only log instead."""
    _clear_test_receipts_and_plans()
    _set_auto_drain(True)
    recipe_id = _pick_recipe_id()
    _bump_pool_to(recipe_id, target=10)
    plan_ids = []
    try:
        for days_ago in (5, 5, 5):
            plan_id, _ = _create_past_day_entry(recipe_id, days_ago=days_ago)
            plan_ids.append(plan_id)
        _trigger_sweep()

        assert _find_alert("meal_reconcile_overdue") is None
        assert _find_suggestion("reconcile_meals_pending") is None
    finally:
        for pid in plan_ids:
            requests.delete(f"{MEAL_PLANS}/{pid}")
