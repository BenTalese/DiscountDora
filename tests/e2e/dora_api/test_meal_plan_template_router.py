"""Meal Plans C-2.F — meal-plan templates.

Covers: snapshot a week's plan as a template; list + detail with offsets;
apply (fork) a template onto a future week; past offsets skipped; saving an
empty week is rejected; editing/deleting a template doesn't touch a plan
forked from it (Decision 1).
"""
from datetime import date, timedelta

import requests

MEAL_PLANS = "http://localhost:5170/api/meal-plans"
TEMPLATES = "http://localhost:5170/api/meal-plan-templates"
RECIPES = "http://localhost:5170/api/recipes"


def _a_recipe_id() -> str:
    resp = requests.get(f"{RECIPES}?limit=1")
    assert resp.status_code == 200, resp.text
    return resp.json()["items"][0]["recipe_id"]


def _monday(weeks_ahead: int) -> date:
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    return this_monday + timedelta(weeks=weeks_ahead)


def _create_plan(monday: date, entries: list[dict]) -> str:
    resp = requests.post(MEAL_PLANS, json={"start_date": monday.isoformat(), "entries": entries})
    assert resp.status_code == 201, resp.text
    return resp.json()["meal_plan_id"]


def _plan(plan_id: str) -> dict:
    resp = requests.get(MEAL_PLANS)
    assert resp.status_code == 200, resp.text
    return next(p for p in resp.json()["items"] if p["meal_plan_id"] == plan_id)


def _save_template(name: str, source_plan_id: str, description: str | None = None) -> str:
    body = {"name": name, "source_meal_plan_id": source_plan_id}
    if description is not None:
        body["description"] = description
    resp = requests.post(TEMPLATES, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["meal_plan_template_id"]


def test_snapshot_list_detail_and_apply_roundtrip():
    recipe_id = _a_recipe_id()
    src_monday = _monday(2)
    plan_id = _create_plan(src_monday, [
        {"recipe_id": recipe_id, "scheduled_for": src_monday.isoformat(), "servings": 2, "slot": "Dinner"},
        {"recipe_id": recipe_id, "scheduled_for": (src_monday + timedelta(days=2)).isoformat(), "servings": 1, "slot": "Lunch"},
    ])
    template_id = None
    applied_plan_id = None
    try:
        template_id = _save_template("Weekday batch", plan_id, description="Two meals")

        mine = next(t for t in requests.get(TEMPLATES).json() if t["meal_plan_template_id"] == template_id)
        assert mine["entry_count"] == 2
        assert mine["name"] == "Weekday batch"
        assert mine["description"] == "Two meals"

        detail = requests.get(f"{TEMPLATES}/{template_id}")
        assert detail.status_code == 200, detail.text
        assert sorted(e["offset_from_monday"] for e in detail.json()["entries"]) == [0, 2]

        target_monday = _monday(4)
        applied = requests.post(f"{MEAL_PLANS}/from-template", json={
            "template_id": template_id,
            "monday_of_week": target_monday.isoformat(),
        })
        assert applied.status_code == 200, applied.text
        body = applied.json()
        assert body["added_count"] == 2
        assert body["skipped_past_count"] == 0
        applied_plan_id = body["meal_plan_id"]

        forked = _plan(applied_plan_id)
        assert sorted(e["scheduled_for"] for e in forked["entries"]) == [
            target_monday.isoformat(),
            (target_monday + timedelta(days=2)).isoformat(),
        ]
    finally:
        if applied_plan_id:
            requests.delete(f"{MEAL_PLANS}/{applied_plan_id}")
        if template_id:
            requests.delete(f"{TEMPLATES}/{template_id}")
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


def test_apply_skips_past_offsets():
    recipe_id = _a_recipe_id()
    src_monday = _monday(2)
    plan_id = _create_plan(src_monday, [
        {"recipe_id": recipe_id, "scheduled_for": src_monday.isoformat(), "servings": 1, "slot": "Dinner"},
    ])
    template_id = None
    try:
        template_id = _save_template("Past-week template", plan_id)
        applied = requests.post(f"{MEAL_PLANS}/from-template", json={
            "template_id": template_id,
            "monday_of_week": _monday(-4).isoformat(),  # fully in the past
        })
        assert applied.status_code == 200, applied.text
        body = applied.json()
        assert body["added_count"] == 0
        assert body["skipped_past_count"] == 1
        assert body["meal_plan_id"] is None  # nothing created
    finally:
        if template_id:
            requests.delete(f"{TEMPLATES}/{template_id}")
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


def test_save_week_with_no_meals_is_rejected():
    monday = _monday(2)
    resp = requests.post(MEAL_PLANS, json={"start_date": monday.isoformat(), "entries": []})
    assert resp.status_code == 201, resp.text
    plan_id = resp.json()["meal_plan_id"]
    try:
        save = requests.post(TEMPLATES, json={"name": "Empty", "source_meal_plan_id": plan_id})
        assert save.status_code == 422, save.text
    finally:
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


def test_editing_or_deleting_template_does_not_touch_forked_plan():
    recipe_id = _a_recipe_id()
    src_monday = _monday(2)
    plan_id = _create_plan(src_monday, [
        {"recipe_id": recipe_id, "scheduled_for": src_monday.isoformat(), "servings": 1, "slot": "Dinner"},
    ])
    template_id = None
    applied_plan_id = None
    try:
        template_id = _save_template("Original name", plan_id)
        applied = requests.post(f"{MEAL_PLANS}/from-template", json={
            "template_id": template_id,
            "monday_of_week": _monday(5).isoformat(),
        })
        applied_plan_id = applied.json()["meal_plan_id"]

        assert requests.patch(f"{TEMPLATES}/{template_id}", json={"name": "Renamed"}).status_code == 204
        assert len(_plan(applied_plan_id)["entries"]) == 1  # unaffected by the rename

        assert requests.delete(f"{TEMPLATES}/{template_id}").status_code == 204
        template_id = None
        assert len(_plan(applied_plan_id)["entries"]) == 1  # survives template deletion
    finally:
        if applied_plan_id:
            requests.delete(f"{MEAL_PLANS}/{applied_plan_id}")
        if template_id:
            requests.delete(f"{TEMPLATES}/{template_id}")
        requests.delete(f"{MEAL_PLANS}/{plan_id}")
