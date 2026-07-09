"""FU-317 Chunk 1 — daily meal-plan reconcile sweep behaviour.

Covers the two branches of `reconcile_consumed_meals` driven by
`AppSetting.auto_drain_past_meals` (D5 install-wide, FU-517):

  * TRUE (default) — sweep continues today's silent auto-drain
    (`MealPlanEntry.consumed_at` set, `Recipe.available_meals`
    decremented) AND writes an `unresolved_auto` receipt per drained
    entry.
  * FALSE — sweep leaves `consumed_at` + `available_meals` untouched
    and writes an `unresolved_manual` receipt per unresolved past-day
    entry.

The sweep fires on the `before_request` hook for the dashboard /
meal-plan / recipe routers (`startup.py`), so every test triggers it
with a cheap `GET /api/meal-plans/today` after arranging the state
it wants.

Cascade + idempotence are covered too — reconcile receipts hang off
`MealPlanEntry` with `ON DELETE CASCADE`; the sweep should never write
a second receipt for the same entry across repeated invocations.
"""
from datetime import date, timedelta

import requests
from sqlalchemy import text

from dora_api.app import db

BASE = "http://localhost:5170/api"
MEAL_PLANS = f"{BASE}/meal-plans"
APP_SETTINGS = f"{BASE}/app-settings"
RECIPES = f"{BASE}/recipes"


# ── helpers ─────────────────────────────────────────────────────────────

def _household_today() -> date:
    return date.fromisoformat(requests.get(f"{MEAL_PLANS}/today").json()["today"])


def _trigger_sweep() -> None:
    """Any GET on the meal-plan router fires the before_request hook."""
    resp = requests.get(f"{MEAL_PLANS}/today")
    assert resp.status_code == 200, resp.text


def _set_auto_drain(value: bool) -> None:
    resp = requests.patch(APP_SETTINGS, json={"auto_drain_past_meals": value})
    assert resp.status_code == 200, resp.text
    assert resp.json()["auto_drain_past_meals"] is value


def _pick_recipe() -> dict:
    """Any seeded recipe with a known `available_meals` pool works."""
    items = requests.get(f"{RECIPES}?limit=1").json()["items"]
    assert items, "seed expected to have at least one recipe"
    return items[0]


def _get_pool(recipe_id: str) -> int:
    resp = requests.get(f"{RECIPES}/{recipe_id}")
    assert resp.status_code == 200, resp.text
    return int(resp.json()["available_meals"])


def _bump_pool(recipe_id: str, target: int) -> None:
    """Set the pool to a known value via the cook endpoint so tests don't
    depend on a specific seed pool count."""
    current = _get_pool(recipe_id)
    delta = target - current
    if delta > 0:
        resp = requests.post(
            f"{RECIPES}/{recipe_id}/cook",
            json={"meals_cooked": delta},
        )
        assert resp.status_code == 200, resp.text


def _create_past_day_entry(recipe_id: str, days_ago: int, servings: int) -> tuple[str, str]:
    """Create a meal plan with one entry scheduled `days_ago` in the past.
    Returns (plan_id, entry_id)."""
    scheduled = _household_today() - timedelta(days=days_ago)
    # `start_date` is the week bucket. Post-day entries are legal; the
    # planner accepts them (see meal_plan create handler validation).
    created = requests.post(MEAL_PLANS, json={
        "start_date": scheduled.isoformat(),
        "entries": [{
            "recipe_id": recipe_id,
            "scheduled_for": scheduled.isoformat(),
            "servings": servings,
            "slot": "Dinner",
        }],
    })
    assert created.status_code in (200, 201), created.text
    body = created.json()
    plan_id = body["meal_plan_id"]
    entry_id = body["entries"][0]["entry_id"]
    return plan_id, entry_id


def _receipts_for(entry_id: str) -> list[dict]:
    """Direct-DB read (no read endpoint yet — that's Chunk 3). Returns
    a list of {state, original_servings, actual_servings} dicts, oldest
    first."""
    with db.engine.connect() as conn:
        rows = conn.execute(
            text(
                'SELECT state, original_servings, actual_servings '
                'FROM "MealPlanReconcileReceipt" '
                'WHERE meal_plan_entry_id = :eid '
                'ORDER BY created_at ASC'
            ),
            {"eid": entry_id},
        ).all()
    return [
        {"state": r[0], "original_servings": r[1], "actual_servings": r[2]}
        for r in rows
    ]


def _entry_consumed_at(entry_id: str) -> str | None:
    with db.engine.connect() as conn:
        row = conn.execute(
            text(
                'SELECT consumed_at FROM "MealPlanEntry" WHERE id = :eid'
            ),
            {"eid": entry_id},
        ).first()
    return None if row is None or row[0] is None else str(row[0])


# ── tests ───────────────────────────────────────────────────────────────

def test__auto_drain_on__writes_unresolved_auto_receipt_and_decrements_pool(api):
    """Default posture: sweep stamps consumed_at, decrements the pool, and
    writes a matching `unresolved_auto` receipt per drained entry."""
    _set_auto_drain(True)
    recipe = _pick_recipe()
    recipe_id = recipe["recipe_id"]
    _bump_pool(recipe_id, target=5)
    pool_before = _get_pool(recipe_id)

    plan_id, entry_id = _create_past_day_entry(recipe_id, days_ago=2, servings=2)
    try:
        _trigger_sweep()

        # Pool dropped by the entry's servings (floored at 0).
        assert _get_pool(recipe_id) == max(0, pool_before - 2)
        # Entry is stamped consumed.
        assert _entry_consumed_at(entry_id) is not None
        # One `unresolved_auto` receipt written.
        receipts = _receipts_for(entry_id)
        assert len(receipts) == 1, receipts
        assert receipts[0]["state"] == "unresolved_auto"
        assert receipts[0]["original_servings"] == 2
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


def test__auto_drain_off__writes_unresolved_manual_receipt_only(api):
    """Manual-confirm posture: sweep does NOT touch consumed_at or the
    pool; it only writes an `unresolved_manual` receipt."""
    _set_auto_drain(False)
    try:
        recipe = _pick_recipe()
        recipe_id = recipe["recipe_id"]
        _bump_pool(recipe_id, target=5)
        pool_before = _get_pool(recipe_id)

        plan_id, entry_id = _create_past_day_entry(recipe_id, days_ago=2, servings=2)
        try:
            _trigger_sweep()

            # Pool unchanged.
            assert _get_pool(recipe_id) == pool_before
            # Entry NOT stamped consumed.
            assert _entry_consumed_at(entry_id) is None
            # One `unresolved_manual` receipt written.
            receipts = _receipts_for(entry_id)
            assert len(receipts) == 1, receipts
            assert receipts[0]["state"] == "unresolved_manual"
            assert receipts[0]["original_servings"] == 2
        finally:
            requests.delete(f"{MEAL_PLANS}/{plan_id}")
    finally:
        _set_auto_drain(True)


def test__sweep_is_idempotent_across_repeated_invocations(api):
    """Firing the sweep multiple times must not produce duplicate
    receipts. Auto-drain ON: idempotent via the `consumed_at IS NULL`
    guard on the UPDATE. Auto-drain OFF: idempotent via the `NOT EXISTS`
    receipt-check on the SELECT."""
    # --- auto-drain ON branch ---
    _set_auto_drain(True)
    recipe = _pick_recipe()
    recipe_id = recipe["recipe_id"]
    _bump_pool(recipe_id, target=5)

    plan_id, entry_id = _create_past_day_entry(recipe_id, days_ago=2, servings=1)
    try:
        _trigger_sweep()
        _trigger_sweep()
        _trigger_sweep()
        receipts = _receipts_for(entry_id)
        assert len(receipts) == 1, f"auto-drain sweep wrote {len(receipts)} receipts, want 1"
        assert receipts[0]["state"] == "unresolved_auto"
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")

    # --- auto-drain OFF branch ---
    _set_auto_drain(False)
    try:
        plan_id, entry_id = _create_past_day_entry(recipe_id, days_ago=2, servings=1)
        try:
            _trigger_sweep()
            _trigger_sweep()
            _trigger_sweep()
            receipts = _receipts_for(entry_id)
            assert len(receipts) == 1, f"manual sweep wrote {len(receipts)} receipts, want 1"
            assert receipts[0]["state"] == "unresolved_manual"
        finally:
            requests.delete(f"{MEAL_PLANS}/{plan_id}")
    finally:
        _set_auto_drain(True)


def test__deleting_a_meal_plan_entry_cascades_to_its_receipts(api):
    """FK is `ON DELETE CASCADE` — a deleted entry must not leave orphan
    receipts in the audit table."""
    _set_auto_drain(True)
    recipe = _pick_recipe()
    recipe_id = recipe["recipe_id"]
    _bump_pool(recipe_id, target=5)

    plan_id, entry_id = _create_past_day_entry(recipe_id, days_ago=2, servings=1)
    _trigger_sweep()
    assert _receipts_for(entry_id), "expected a receipt to exist before delete"

    # Deleting the whole plan cascades through MealPlanEntry → Receipt.
    resp = requests.delete(f"{MEAL_PLANS}/{plan_id}")
    assert resp.status_code in (200, 204), resp.text
    assert _receipts_for(entry_id) == [], "receipt should have cascaded away"
