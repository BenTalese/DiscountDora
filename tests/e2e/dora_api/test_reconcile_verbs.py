"""FU-317 Chunk 3 — reconcile queue + per-entry verb endpoints.

Covers the surface Chunk 5 (SPA) will call — not the sweep itself
(that's Chunk 1's `test_reconcile_receipts.py`). Every test creates a
past-day plan, lets the sweep drop a receipt, then hits
`POST /api/meal-plans/reconcile/<entry_id>` with a verb and asserts
the pool + `consumed_at` + receipt state converged as the proposal §3.2
locked.
"""
from datetime import date, timedelta

import requests
from sqlalchemy import text

from dora_api.app import db

BASE = "http://localhost:5170/api"
MEAL_PLANS = f"{BASE}/meal-plans"
APP_SETTINGS = f"{BASE}/app-settings"
RECIPES = f"{BASE}/recipes"


# ── helpers (mostly copied from test_reconcile_receipts.py) ─────────────

def _household_today() -> date:
    return date.fromisoformat(requests.get(f"{MEAL_PLANS}/today").json()["today"])


def _trigger_sweep() -> None:
    resp = requests.get(f"{MEAL_PLANS}/today")
    assert resp.status_code == 200, resp.text


def _set_auto_drain(value: bool) -> None:
    resp = requests.patch(APP_SETTINGS, json={"auto_drain_past_meals": value})
    assert resp.status_code == 200, resp.text


def _pick_recipe() -> dict:
    items = requests.get(f"{RECIPES}?limit=1").json()["items"]
    assert items, "seed expected to have at least one recipe"
    return items[0]


def _get_pool(recipe_id: str) -> int:
    resp = requests.get(f"{RECIPES}/{recipe_id}")
    assert resp.status_code == 200, resp.text
    return int(resp.json()["available_meals"])


def _bump_pool(recipe_id: str, target: int) -> None:
    current = _get_pool(recipe_id)
    delta = target - current
    if delta > 0:
        resp = requests.post(
            f"{RECIPES}/{recipe_id}/cook",
            json={"meals_cooked": delta},
        )
        assert resp.status_code == 200, resp.text


def _create_past_day_entry(recipe_id: str, days_ago: int, servings: int):
    scheduled = _household_today() - timedelta(days=days_ago)
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
    return body["meal_plan_id"], body["entries"][0]["entry_id"]


def _receipts_for(entry_id: str) -> list[dict]:
    with db.engine.connect() as conn:
        rows = conn.execute(
            text(
                'SELECT state, original_servings, actual_servings, cooked_on '
                'FROM "MealPlanReconcileReceipt" '
                'WHERE meal_plan_entry_id = :eid '
                'ORDER BY created_at ASC'
            ),
            {"eid": entry_id},
        ).all()
    return [
        {"state": r[0], "original_servings": r[1], "actual_servings": r[2],
         "cooked_on": (r[3].isoformat() if hasattr(r[3], "isoformat") else r[3])}
        for r in rows
    ]


def _entry_consumed_at(entry_id: str):
    with db.engine.connect() as conn:
        row = conn.execute(
            text('SELECT consumed_at FROM "MealPlanEntry" WHERE id = :eid'),
            {"eid": entry_id},
        ).first()
    return None if row is None or row[0] is None else str(row[0])


# ── Queue endpoint ──────────────────────────────────────────────────────

def test__queue_lists_only_entries_with_unresolved_latest_receipt(api):
    _set_auto_drain(True)
    recipe = _pick_recipe()
    _bump_pool(recipe["recipe_id"], target=5)
    plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=2, servings=1)
    try:
        _trigger_sweep()
        listing = requests.get(f"{MEAL_PLANS}/reconcile-queue").json()
        assert entry_id in {e["entry_id"] for e in listing["entries"]}, listing
        assert listing["total"] >= 1

        # Resolve the entry → it drops out of the queue.
        resp = requests.post(
            f"{MEAL_PLANS}/reconcile/{entry_id}",
            json={"verb": "cooked"},
        )
        assert resp.status_code == 200, resp.text

        listing_after = requests.get(f"{MEAL_PLANS}/reconcile-queue").json()
        assert entry_id not in {e["entry_id"] for e in listing_after["entries"]}, listing_after
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


def test__include_resolved_flag_returns_empty_in_mvp(api):
    """Impl-plan Chunk 3: history view is out of scope for MVP — the
    param is accepted but returns empty until Chunk 5 wires it."""
    resp = requests.get(f"{MEAL_PLANS}/reconcile-queue?include_resolved=true")
    assert resp.status_code == 200
    assert resp.json() == {"entries": [], "next_cursor": None, "total": 0}


# ── Verb: cooked (as planned) ───────────────────────────────────────────

def test__verb_cooked_on_auto_drain_on__no_pool_change_and_writes_resolved_confirmed(api):
    """Under auto-drain ON, the sweep has already stamped consumed_at and
    decremented the pool. Cooked-as-planned just writes a resolved_confirmed
    receipt — the world state is already right."""
    _set_auto_drain(True)
    recipe = _pick_recipe()
    _bump_pool(recipe["recipe_id"], target=5)
    plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=2, servings=2)
    try:
        _trigger_sweep()
        pool_after_sweep = _get_pool(recipe["recipe_id"])  # already decremented by 2

        resp = requests.post(
            f"{MEAL_PLANS}/reconcile/{entry_id}",
            json={"verb": "cooked"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["receipt"]["state"] == "resolved_confirmed"
        assert body["new_pool"] == pool_after_sweep, "no pool delta expected"
        assert _entry_consumed_at(entry_id) is not None
        # Two receipts: unresolved_auto (sweep) + resolved_confirmed (verb).
        states = [r["state"] for r in _receipts_for(entry_id)]
        assert states == ["unresolved_auto", "resolved_confirmed"], states
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


def test__verb_cooked_on_auto_drain_off__stamps_consumed_and_decrements_pool(api):
    """Under auto-drain OFF, the sweep left everything untouched. Cooked
    now applies the drain."""
    _set_auto_drain(False)
    try:
        recipe = _pick_recipe()
        _bump_pool(recipe["recipe_id"], target=5)
        plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=2, servings=2)
        try:
            _trigger_sweep()
            pool_before = _get_pool(recipe["recipe_id"])
            assert _entry_consumed_at(entry_id) is None

            resp = requests.post(
                f"{MEAL_PLANS}/reconcile/{entry_id}",
                json={"verb": "cooked"},
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert body["receipt"]["state"] == "resolved_confirmed"
            assert body["new_pool"] == pool_before - 2
            assert _entry_consumed_at(entry_id) is not None
        finally:
            requests.delete(f"{MEAL_PLANS}/{plan_id}")
    finally:
        _set_auto_drain(True)


# ── Verb: not_cooked ────────────────────────────────────────────────────

def test__verb_not_cooked_on_auto_drain_on__undoes_the_drain(api):
    """Under auto-drain ON, the sweep drained. `not_cooked` gives it
    back: pool += servings, consumed_at = NULL, receipt =
    resolved_not_cooked."""
    _set_auto_drain(True)
    recipe = _pick_recipe()
    _bump_pool(recipe["recipe_id"], target=5)
    plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=2, servings=2)
    try:
        _trigger_sweep()
        pool_after_sweep = _get_pool(recipe["recipe_id"])  # 5 - 2 = 3

        resp = requests.post(
            f"{MEAL_PLANS}/reconcile/{entry_id}",
            json={"verb": "not_cooked"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["receipt"]["state"] == "resolved_not_cooked"
        assert body["new_pool"] == pool_after_sweep + 2, "drain undone"
        assert _entry_consumed_at(entry_id) is None
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


# ── Verb: cooked_adjusted ───────────────────────────────────────────────

def test__verb_cooked_adjusted_on_auto_drain_on__reflows_the_pool_delta(api):
    """Sweep drained by original_servings=2. User says 'actually I made 5';
    pool needs to go DOWN by another 3."""
    _set_auto_drain(True)
    recipe = _pick_recipe()
    _bump_pool(recipe["recipe_id"], target=10)
    plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=2, servings=2)
    try:
        _trigger_sweep()
        pool_after_sweep = _get_pool(recipe["recipe_id"])  # 10 - 2 = 8

        resp = requests.post(
            f"{MEAL_PLANS}/reconcile/{entry_id}",
            json={"verb": "cooked_adjusted", "actual_servings": 5},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["receipt"]["state"] == "resolved_adjusted"
        assert body["receipt"]["actual_servings"] == 5
        assert body["new_pool"] == pool_after_sweep - 3
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


def test__verb_cooked_adjusted_requires_actual_servings(api):
    _set_auto_drain(True)
    recipe = _pick_recipe()
    _bump_pool(recipe["recipe_id"], target=5)
    plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=2, servings=1)
    try:
        _trigger_sweep()
        resp = requests.post(
            f"{MEAL_PLANS}/reconcile/{entry_id}",
            json={"verb": "cooked_adjusted"},
        )
        assert resp.status_code == 400, resp.text
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


# ── Verb: cooked_later ──────────────────────────────────────────────────

def test__verb_cooked_later_writes_cooked_on_on_receipt(api):
    _set_auto_drain(True)
    recipe = _pick_recipe()
    _bump_pool(recipe["recipe_id"], target=5)
    plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=3, servings=1)
    try:
        _trigger_sweep()
        cooked_on = (_household_today() - timedelta(days=1)).isoformat()
        resp = requests.post(
            f"{MEAL_PLANS}/reconcile/{entry_id}",
            json={"verb": "cooked_later", "cooked_on": cooked_on},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["receipt"]["state"] == "resolved_confirmed"
        assert body["receipt"]["cooked_on"] == cooked_on
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


# ── Verb: skip ──────────────────────────────────────────────────────────

def test__verb_skip_keeps_entry_in_queue_next_visit(api):
    """`skip` writes a resolved_deferred receipt (small side effect —
    the queue filter treats deferred as still-unresolved)."""
    _set_auto_drain(True)
    recipe = _pick_recipe()
    _bump_pool(recipe["recipe_id"], target=5)
    plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=2, servings=1)
    try:
        _trigger_sweep()
        resp = requests.post(
            f"{MEAL_PLANS}/reconcile/{entry_id}",
            json={"verb": "skip"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["receipt"]["state"] == "resolved_deferred"
        listing = requests.get(f"{MEAL_PLANS}/reconcile-queue").json()
        assert entry_id in {e["entry_id"] for e in listing["entries"]}, listing
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


# ── Idempotence + change-of-mind ────────────────────────────────────────

def test__same_verb_replay_is_idempotent(api):
    """Second `cooked` call returns 200 with `idempotent: true` and does
    not add another receipt."""
    _set_auto_drain(True)
    recipe = _pick_recipe()
    _bump_pool(recipe["recipe_id"], target=5)
    plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=2, servings=1)
    try:
        _trigger_sweep()
        r1 = requests.post(f"{MEAL_PLANS}/reconcile/{entry_id}", json={"verb": "cooked"})
        assert r1.json()["idempotent"] is False
        r2 = requests.post(f"{MEAL_PLANS}/reconcile/{entry_id}", json={"verb": "cooked"})
        assert r2.json()["idempotent"] is True
        states = [r["state"] for r in _receipts_for(entry_id)]
        assert states == ["unresolved_auto", "resolved_confirmed"], states
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


def test__change_of_mind_writes_new_receipt_and_reverses_pool(api):
    """Cooked → resolved_confirmed. Then user says Didn't cook → new
    resolved_not_cooked receipt, pool goes back up, consumed_at NULL."""
    _set_auto_drain(True)
    recipe = _pick_recipe()
    _bump_pool(recipe["recipe_id"], target=5)
    plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=2, servings=1)
    try:
        _trigger_sweep()
        pool_after_sweep = _get_pool(recipe["recipe_id"])  # 5 - 1 = 4

        r1 = requests.post(f"{MEAL_PLANS}/reconcile/{entry_id}", json={"verb": "cooked"})
        assert r1.status_code == 200
        # No pool change vs sweep (still 4).
        assert _get_pool(recipe["recipe_id"]) == pool_after_sweep

        r2 = requests.post(f"{MEAL_PLANS}/reconcile/{entry_id}", json={"verb": "not_cooked"})
        assert r2.status_code == 200
        assert r2.json()["receipt"]["state"] == "resolved_not_cooked"
        # Pool restored (4 + 1 = 5).
        assert _get_pool(recipe["recipe_id"]) == pool_after_sweep + 1
        assert _entry_consumed_at(entry_id) is None
        states = [r["state"] for r in _receipts_for(entry_id)]
        assert states == ["unresolved_auto", "resolved_confirmed", "resolved_not_cooked"], states
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


# ── Validation + auth ───────────────────────────────────────────────────

def test__unknown_verb_returns_400(api):
    _set_auto_drain(True)
    recipe = _pick_recipe()
    _bump_pool(recipe["recipe_id"], target=5)
    plan_id, entry_id = _create_past_day_entry(recipe["recipe_id"], days_ago=2, servings=1)
    try:
        _trigger_sweep()
        resp = requests.post(
            f"{MEAL_PLANS}/reconcile/{entry_id}",
            json={"verb": "hallucinate"},
        )
        assert resp.status_code == 400, resp.text
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


def test__unknown_entry_id_returns_404(api):
    resp = requests.post(
        f"{MEAL_PLANS}/reconcile/00000000-0000-0000-0000-000000000000",
        json={"verb": "cooked"},
    )
    assert resp.status_code == 404, resp.text
