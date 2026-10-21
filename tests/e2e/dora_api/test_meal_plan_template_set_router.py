"""Meal Plans C-2.G — template sets (rotating) + recurring apply.

Covers: set CRUD + reorder; recurring apply of a single template over a range;
recurring apply of a set rotates templates by week; the 26-week cap; and the
exactly-one-source rule.
"""
from datetime import date, timedelta

import requests

MEAL_PLANS = "http://localhost:5170/api/meal-plans"
TEMPLATES = "http://localhost:5170/api/meal-plan-templates"
SETS = "http://localhost:5170/api/meal-plan-template-sets"
RECIPES = "http://localhost:5170/api/recipes"


def _a_recipe_id() -> str:
    return requests.get(f"{RECIPES}?limit=1").json()["items"][0]["recipe_id"]


def _monday(weeks_ahead: int) -> date:
    today = date.today()
    return (today - timedelta(days=today.weekday())) + timedelta(weeks=weeks_ahead)


def _create_plan(monday: date, entries: list[dict]) -> str:
    resp = requests.post(MEAL_PLANS, json={"start_date": monday.isoformat(), "entries": entries})
    assert resp.status_code == 201, resp.text
    return resp.json()["meal_plan_id"]


def _template_on_day(recipe_id: str, monday: date, offset: int, slot: str) -> tuple[str, str]:
    """Returns (template_id, source_plan_id) for a one-meal template on a day."""
    plan_id = _create_plan(monday, [{
        "recipe_id": recipe_id,
        "scheduled_for": (monday + timedelta(days=offset)).isoformat(),
        "servings": 1,
        "slot": slot,
    }])
    resp = requests.post(TEMPLATES, json={"name": f"T+{offset}", "source_meal_plan_id": plan_id})
    assert resp.status_code == 201, resp.text
    return resp.json()["meal_plan_template_id"], plan_id


def _plans():
    return requests.get(MEAL_PLANS).json()["items"]


def _plan_for_monday(monday: date) -> dict | None:
    iso = monday.isoformat()
    return next((p for p in _plans() if p["start_date"] == iso), None)


def test_set_crud_and_reorder():
    recipe_id = _a_recipe_id()
    (ta, pa), (tb, pb) = _template_on_day(recipe_id, _monday(2), 0, "Dinner"), _template_on_day(recipe_id, _monday(2), 1, "Lunch")
    set_id = None
    try:
        created = requests.post(SETS, json={"name": "Rotation", "template_ids": [ta, tb]})
        assert created.status_code == 201, created.text
        set_id = created.json()["meal_plan_template_set_id"]

        summary = next(s for s in requests.get(SETS).json() if s["meal_plan_template_set_id"] == set_id)
        assert summary["item_count"] == 2

        detail = requests.get(f"{SETS}/{set_id}").json()
        assert [i["template_id"] for i in detail["items"]] == [ta, tb]

        # Reorder.
        assert requests.patch(f"{SETS}/{set_id}", json={"template_ids": [tb, ta]}).status_code == 204
        detail = requests.get(f"{SETS}/{set_id}").json()
        assert [i["template_id"] for i in detail["items"]] == [tb, ta]

        # Unknown template id rejected.
        bad = requests.post(SETS, json={"name": "Bad", "template_ids": ["00000000-0000-0000-0000-000000000000"]})
        assert bad.status_code == 422, bad.text
    finally:
        if set_id:
            requests.delete(f"{SETS}/{set_id}")
        requests.delete(f"{TEMPLATES}/{ta}")
        requests.delete(f"{TEMPLATES}/{tb}")
        requests.delete(f"{MEAL_PLANS}/{pa}")
        requests.delete(f"{MEAL_PLANS}/{pb}")


def test_recurring_single_template():
    recipe_id = _a_recipe_id()
    ta, pa = _template_on_day(recipe_id, _monday(2), 0, "Dinner")
    weeks = [_monday(4), _monday(5), _monday(6)]
    try:
        resp = requests.post(f"{MEAL_PLANS}/from-template/recurring", json={
            "template_id": ta,
            "start_monday": weeks[0].isoformat(),
            "end_monday": weeks[-1].isoformat(),
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["weeks_applied"] == 3
        assert body["total_added"] == 3
        for m in weeks:
            assert _plan_for_monday(m) is not None
    finally:
        for m in weeks:
            p = _plan_for_monday(m)
            if p:
                requests.delete(f"{MEAL_PLANS}/{p['meal_plan_id']}")
        requests.delete(f"{TEMPLATES}/{ta}")
        requests.delete(f"{MEAL_PLANS}/{pa}")


def test_recurring_set_rotates_by_week():
    recipe_id = _a_recipe_id()
    src = _monday(2)
    ta, pa = _template_on_day(recipe_id, src, 0, "Dinner")  # meal on Monday
    tb, pb = _template_on_day(recipe_id, src, 1, "Lunch")   # meal on Tuesday
    set_id = None
    weeks = [_monday(8), _monday(9), _monday(10)]
    try:
        set_id = requests.post(SETS, json={"name": "AB rotation", "template_ids": [ta, tb]}).json()["meal_plan_template_set_id"]
        resp = requests.post(f"{MEAL_PLANS}/from-template/recurring", json={
            "template_set_id": set_id,
            "start_monday": weeks[0].isoformat(),
            "end_monday": weeks[-1].isoformat(),
        })
        assert resp.status_code == 200, resp.text
        assert resp.json()["weeks_applied"] == 3

        # week0 → A (Mon), week1 → B (Tue), week2 → A (Mon).
        expected_offsets = [0, 1, 0]
        for m, off in zip(weeks, expected_offsets):
            plan = _plan_for_monday(m)
            assert plan is not None, m
            days = [e["scheduled_for"] for e in plan["entries"]]
            assert days == [(m + timedelta(days=off)).isoformat()], (m, off, days)
    finally:
        for m in weeks:
            p = _plan_for_monday(m)
            if p:
                requests.delete(f"{MEAL_PLANS}/{p['meal_plan_id']}")
        if set_id:
            requests.delete(f"{SETS}/{set_id}")
        requests.delete(f"{TEMPLATES}/{ta}")
        requests.delete(f"{TEMPLATES}/{tb}")
        requests.delete(f"{MEAL_PLANS}/{pa}")
        requests.delete(f"{MEAL_PLANS}/{pb}")


def test_recurring_range_cap_and_source_rules():
    recipe_id = _a_recipe_id()
    ta, pa = _template_on_day(recipe_id, _monday(2), 0, "Dinner")
    try:
        # > 26 weeks → rejected.
        over = requests.post(f"{MEAL_PLANS}/from-template/recurring", json={
            "template_id": ta,
            "start_monday": _monday(2).isoformat(),
            "end_monday": _monday(30).isoformat(),
        })
        assert over.status_code == 422, over.text

        # Neither source → rejected.
        neither = requests.post(f"{MEAL_PLANS}/from-template/recurring", json={
            "start_monday": _monday(2).isoformat(),
            "end_monday": _monday(3).isoformat(),
        })
        assert neither.status_code == 422, neither.text
    finally:
        requests.delete(f"{TEMPLATES}/{ta}")
        requests.delete(f"{MEAL_PLANS}/{pa}")
