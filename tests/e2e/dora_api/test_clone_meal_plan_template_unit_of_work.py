"""FU-512 — `POST /meal-plan-templates/<id>/clone` is a unit of work.

Pre-FU-512 committed twice (clone row, then entries) and skipped the second
commit when the source had no entries. Now: one commit, and an empty-entries
source still commits the clone (a no-op save on just the template row).
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


def test__clone_meal_plan_template__with_entries__commits_clone_and_entries_together(api):
    recipe_id = _a_recipe_id()
    src_monday = _monday(5)
    plan_resp = requests.post(MEAL_PLANS, json={
        "start_date": src_monday.isoformat(),
        "entries": [
            {"recipe_id": recipe_id, "scheduled_for": src_monday.isoformat(),
             "servings": 3, "slot": "Dinner"},
        ],
    })
    assert plan_resp.status_code == 201, plan_resp.text
    plan_id = plan_resp.json()["meal_plan_id"]

    src_template_id = None
    clone_template_id = None
    try:
        src_resp = requests.post(TEMPLATES, json={
            "name": f"FU-512 source {uuid4()}",
            "source_meal_plan_id": plan_id,
        })
        assert src_resp.status_code == 201, src_resp.text
        src_template_id = src_resp.json()["meal_plan_template_id"]

        clone_resp = requests.post(f"{TEMPLATES}/{src_template_id}/clone")
        assert clone_resp.status_code == 201, clone_resp.text
        clone_template_id = clone_resp.json()["meal_plan_template_id"]

        detail = requests.get(f"{TEMPLATES}/{clone_template_id}")
        assert detail.status_code == 200, detail.text
        assert len(detail.json()["entries"]) == 1
    finally:
        if clone_template_id:
            requests.delete(f"{TEMPLATES}/{clone_template_id}")
        if src_template_id:
            requests.delete(f"{TEMPLATES}/{src_template_id}")
        requests.delete(f"{MEAL_PLANS}/{plan_id}")
