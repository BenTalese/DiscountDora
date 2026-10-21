"""FU-512 — `POST /meal-plan-template-sets` is a unit of work.

Pre-FU-512 committed twice (set row, then item rows). `missing_template_ids`
returns pre-commit, so a rollback test can't distinguish pre/post-refactor —
happy-path only.
"""
from datetime import date, timedelta
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
MEAL_PLANS = f"{BASE}/meal-plans"
TEMPLATES = f"{BASE}/meal-plan-templates"
SETS = f"{BASE}/meal-plan-template-sets"
RECIPES = f"{BASE}/recipes"


def _a_recipe_id() -> str:
    return requests.get(f"{RECIPES}?limit=1").json()["items"][0]["recipe_id"]


def _monday(weeks_ahead: int) -> date:
    today = date.today()
    return today - timedelta(days=today.weekday()) + timedelta(weeks=weeks_ahead)


def test__create_template_set__with_items__commits_set_and_items_together(api):
    recipe_id = _a_recipe_id()
    src_monday = _monday(7)
    plan_resp = requests.post(MEAL_PLANS, json={
        "start_date": src_monday.isoformat(),
        "entries": [
            {"recipe_id": recipe_id, "scheduled_for": src_monday.isoformat(),
             "servings": 1, "slot": "Dinner"},
        ],
    })
    plan_id = plan_resp.json()["meal_plan_id"]

    tid1 = tid2 = set_id = None
    try:
        t1 = requests.post(TEMPLATES, json={
            "name": f"FU-512 T1 {uuid4()}", "source_meal_plan_id": plan_id,
        })
        tid1 = t1.json()["meal_plan_template_id"]
        t2 = requests.post(TEMPLATES, json={
            "name": f"FU-512 T2 {uuid4()}", "source_meal_plan_id": plan_id,
        })
        tid2 = t2.json()["meal_plan_template_id"]

        resp = requests.post(SETS, json={
            "name": f"FU-512 set {uuid4()}",
            "template_ids": [tid1, tid2],
        })
        assert resp.status_code == 201, resp.text
        set_id = resp.json()["meal_plan_template_set_id"]

        detail = requests.get(f"{SETS}/{set_id}")
        assert detail.status_code == 200, detail.text
        assert len(detail.json()["items"]) == 2
    finally:
        if set_id:
            requests.delete(f"{SETS}/{set_id}")
        if tid1:
            requests.delete(f"{TEMPLATES}/{tid1}")
        if tid2:
            requests.delete(f"{TEMPLATES}/{tid2}")
        requests.delete(f"{MEAL_PLANS}/{plan_id}")


def test__create_template_set__empty__commits_the_set(api):
    resp = requests.post(SETS, json={
        "name": f"FU-512 empty set {uuid4()}",
        "template_ids": [],
    })
    assert resp.status_code == 201, resp.text
    set_id = resp.json()["meal_plan_template_set_id"]
    try:
        detail = requests.get(f"{SETS}/{set_id}")
        assert detail.status_code == 200, detail.text
        assert detail.json()["items"] == []
    finally:
        requests.delete(f"{SETS}/{set_id}")
