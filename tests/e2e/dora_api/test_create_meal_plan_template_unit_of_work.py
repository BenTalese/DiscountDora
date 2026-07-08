"""FU-512 — `POST /meal-plan-templates` is a unit of work.

The pre-FU-512 handler committed twice (template row, then entry rows). This
pins the invariant that a snapshot is now one transaction.

No reachable failure surface exists between the two former commits
(`source_not_found` and `no_entries` both return before the first add), so
this is a shape-uniformity change: only a happy-path assertion.
"""
from datetime import date, timedelta
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
MEAL_PLANS = f"{BASE}/meal-plans"
TEMPLATES = f"{BASE}/meal-plan-templates"
RECIPES = f"{BASE}/recipes"


def _a_recipe_id() -> str:
    return requests.get(f"{RECIPES}?limit=1").json()["items"][0]["recipe_id"]


def _monday(weeks_ahead: int) -> date:
    today = date.today()
    return today - timedelta(days=today.weekday()) + timedelta(weeks=weeks_ahead)


def test__create_meal_plan_template__all_valid__commits_template_and_entries_together(api):
    recipe_id = _a_recipe_id()
    src_monday = _monday(3)
    plan_resp = requests.post(MEAL_PLANS, json={
        "start_date": src_monday.isoformat(),
        "entries": [
            {"recipe_id": recipe_id, "scheduled_for": src_monday.isoformat(),
             "servings": 2, "slot": "Dinner"},
            {"recipe_id": recipe_id,
             "scheduled_for": (src_monday + timedelta(days=1)).isoformat(),
             "servings": 1, "slot": "Lunch"},
        ],
    })
    assert plan_resp.status_code == 201, plan_resp.text
    plan_id = plan_resp.json()["meal_plan_id"]

    template_id = None
    try:
        name = f"FU-512 template {uuid4()}"
        resp = requests.post(TEMPLATES, json={
            "name": name, "source_meal_plan_id": plan_id,
        })
        assert resp.status_code == 201, resp.text
        template_id = resp.json()["meal_plan_template_id"]

        detail = requests.get(f"{TEMPLATES}/{template_id}")
        assert detail.status_code == 200, detail.text
        assert len(detail.json()["entries"]) == 2
    finally:
        if template_id:
            requests.delete(f"{TEMPLATES}/{template_id}")
        requests.delete(f"{MEAL_PLANS}/{plan_id}")
