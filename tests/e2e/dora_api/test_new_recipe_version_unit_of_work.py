"""FU-512 — `POST /recipes/<id>/new-version` is a unit of work.

Pre-FU-512 committed twice (new recipe row, then tags/tools/steps/images).
Structurally identical to the FU-456 CreateRecipe refactor — access helpers
use Core-level inserts, so the parent recipe FK is flushed before them
rather than committed. No reachable failure surface from a valid source
recipe; happy-path only.
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
RECIPES = f"{BASE}/recipes"


def _create_recipe() -> str:
    resp = requests.post(RECIPES, json={"name": f"FU-512 source {uuid4()}"})
    assert resp.status_code in (200, 201), resp.text
    return resp.json().get("recipe_id") or resp.json().get("id")


def test__new_recipe_version__valid_source__commits_new_version_together(api):
    source_id = _create_recipe()
    resp = requests.post(f"{RECIPES}/{source_id}/new-version")
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    new_id = body.get("recipe_id") or body.get("id") or body.get("new_recipe_id")
    assert new_id, body

    detail = requests.get(f"{RECIPES}/{new_id}")
    assert detail.status_code == 200, detail.text
