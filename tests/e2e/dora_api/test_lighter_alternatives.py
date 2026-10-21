"""FU-637 — lighter alternatives over the real request path.

The ranking rules are pinned in `tests/test_lighter_swaps.py`. What only a real
request proves: the endpoint finds the entry, nutrition-mode gating, and — the
one that matters — that applying a lighter swap works **with money switched
off**. The apply path was built for budget defence and carried a
`money_enabled` gate; a lighter swap has nothing to do with money, and
inheriting that gate by accident would have made the feature silently dead on
any install that doesn't track spend.
"""
from datetime import date
from uuid import uuid4

import requests

from tests.support import assert_problem

BASE = "http://localhost:5170/api"
MEAL_PLANS = f"{BASE}/meal-plans"
RECIPES = f"{BASE}/recipes"
APP_SETTINGS = f"{BASE}/app-settings"


def _set_settings(**fields) -> None:
    resp = requests.patch(APP_SETTINGS, json=fields)
    assert resp.status_code in (200, 204), resp.text


def _household_today() -> date:
    return date.fromisoformat(requests.get(f"{MEAL_PLANS}/today").json()["today"])


def _slot() -> str:
    return requests.get(f"{BASE}/meal-slots").json()[0]["name"]


def _recipe(kcal: int, *, cuisine_id: str | None = None, last_made: str | None = None) -> str:
    body = {"name": f"lighter-{uuid4().hex[:8]}", "kcal": kcal, "servings": 2}
    if cuisine_id:
        body["cuisine_id"] = cuisine_id
    if last_made:
        body["last_made_on"] = last_made
    resp = requests.post(RECIPES, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["recipe_id"]


def _cuisine() -> str:
    resp = requests.post(f"{BASE}/cuisines", json={"name": f"Lighter {uuid4().hex[:6]}"})
    assert resp.status_code == 201, resp.text
    return resp.json()["cuisine_id"]


def _plan_with_meal(recipe_id: str) -> tuple[str, str]:
    """Returns (plan_id, entry_id) for a single planned meal today."""
    resp = requests.post(MEAL_PLANS, json={
        "name": f"lighter plan {uuid4().hex[:8]}",
        "start_date": _household_today().isoformat(),
        "entries": [{
            "recipe_id": recipe_id,
            "scheduled_for": _household_today().isoformat(),
            "servings": 2,
            "slot": _slot(),
        }],
    })
    assert resp.status_code == 201, resp.text
    plan_id = resp.json()["meal_plan_id"]
    plan = requests.get(f"{MEAL_PLANS}?filter=meal_plan_id:eq:{plan_id}").json()["items"][0]
    return plan_id, plan["entries"][0]["meal_plan_entry_id"]


def _alternatives(plan_id: str, entry_id: str) -> dict:
    resp = requests.get(f"{MEAL_PLANS}/{plan_id}/lighter-alternatives?entry_id={entry_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


def test__lighter_alternatives__OffersALighterMealOfTheSameStyle(api):
    _set_settings(nutrition_mode="simple")
    cuisine = _cuisine()
    heavy = _recipe(900, cuisine_id=cuisine)
    _recipe(500, cuisine_id=cuisine)          # the lighter option
    _recipe(1100, cuisine_id=cuisine)         # heavier — must not be offered
    plan_id, entry_id = _plan_with_meal(heavy)

    body = _alternatives(plan_id, entry_id)

    assert body["from_kcal_per_serving"] == 900
    names = {c["to_recipe_name"]: c for c in body["candidates"]}
    assert len(names) >= 1
    for candidate in names.values():
        assert candidate["kcal_per_serving"] < 900
        assert candidate["saved_kcal"] == 900 - candidate["kcal_per_serving"]
        assert candidate["reason_chip"].startswith("lighter_recipe_")


def test__lighter_alternatives__NutritionOff__AnswersEmptyRatherThanErroring(api):
    _set_settings(nutrition_mode="simple")
    cuisine = _cuisine()
    heavy = _recipe(900, cuisine_id=cuisine)
    _recipe(400, cuisine_id=cuisine)
    plan_id, entry_id = _plan_with_meal(heavy)

    _set_settings(nutrition_mode="off")
    try:
        body = _alternatives(plan_id, entry_id)
        # "Nothing to offer" is a normal answer here, not a failure.
        assert body["candidates"] == []
    finally:
        _set_settings(nutrition_mode="simple")


def test__lighter_alternatives__UnknownEntry__404s(api):
    _set_settings(nutrition_mode="simple")
    plan_id, _ = _plan_with_meal(_recipe(700))

    resp = requests.get(f"{MEAL_PLANS}/{plan_id}/lighter-alternatives?entry_id={uuid4()}")
    assert_problem(resp, 404)


def test__lighter_alternatives__MissingEntryId__400s(api):
    plan_id, _ = _plan_with_meal(_recipe(700))

    assert_problem(requests.get(f"{MEAL_PLANS}/{plan_id}/lighter-alternatives"), 400)


def test__apply_swap__LighterReason__WorksWithMoneyOff(api):
    """The regression this whole test file exists for."""
    _set_settings(nutrition_mode="simple", money_enabled=False)
    cuisine = _cuisine()
    heavy = _recipe(900, cuisine_id=cuisine)
    light = _recipe(400, cuisine_id=cuisine)
    plan_id, entry_id = _plan_with_meal(heavy)

    resp = requests.post(f"{MEAL_PLANS}/{plan_id}/apply-swap", json={
        "kind": "recipe",
        "entry_id": entry_id,
        "to_recipe_id": light,
        "reason": "lighter",
    })
    assert resp.status_code == 200, resp.text

    plan = requests.get(f"{MEAL_PLANS}?filter=meal_plan_id:eq:{plan_id}").json()["items"][0]
    assert plan["entries"][0]["recipe_id"] == light

    # And it's undoable exactly like a budget swap — one ledger, one reversal.
    undo = requests.post(f"{MEAL_PLANS}/{plan_id}/undo-swap", json={
        "swap_ledger_id": resp.json()["swap_ledger_id"],
    })
    assert undo.status_code == 200, undo.text
    plan = requests.get(f"{MEAL_PLANS}?filter=meal_plan_id:eq:{plan_id}").json()["items"][0]
    assert plan["entries"][0]["recipe_id"] == heavy


def test__apply_swap__BudgetReasonWithMoneyOff__StillRefused(api):
    # The gate wasn't removed, it was scoped to the axis that owns it.
    _set_settings(money_enabled=False)
    heavy = _recipe(900)
    light = _recipe(400)
    plan_id, entry_id = _plan_with_meal(heavy)

    resp = requests.post(f"{MEAL_PLANS}/{plan_id}/apply-swap", json={
        "kind": "recipe", "entry_id": entry_id, "to_recipe_id": light,
    })
    assert_problem(resp, 422)


def test__apply_swap__UnknownReason__400s(api):
    _set_settings(nutrition_mode="simple")
    plan_id, entry_id = _plan_with_meal(_recipe(900))

    resp = requests.post(f"{MEAL_PLANS}/{plan_id}/apply-swap", json={
        "kind": "recipe", "entry_id": entry_id, "to_recipe_id": _recipe(400),
        "reason": "vibes",
    })
    assert_problem(resp, 400)
