"""FU-456 — `POST /recipes` is a unit of work.

Before FU-456 the handler committed 5 times (recipe → sections → tags →
steps → images), so a validation failure on tags left the recipe row +
sections behind. These tests pin down the invariant that the whole
create is now one transaction: an invalid sub-part 400s and no row
persists.
"""
from uuid import uuid4

import requests

BASE = 'http://localhost:5170/api'
RECIPES = f"{BASE}/recipes"


def _recipe_count() -> int:
    return len(requests.get(f"{RECIPES}?limit=500").json()["items"])


def _find_recipe_by_name(name: str):
    for r in requests.get(f"{RECIPES}?limit=500").json()["items"]:
        if r.get("name") == name:
            return r
    return None


def test__create_recipe__invalid_dietary_tag__rolls_back_the_whole_recipe(api):
    """Bogus dietary_tag_id → 400, recipe row does NOT persist."""
    before = _recipe_count()
    name = f"FU-456 rollback probe {uuid4()}"
    resp = requests.post(RECIPES, json={
        "name": name,
        "dietary_tag_ids": [str(uuid4())],  # unknown tag id
    })
    assert resp.status_code == 400, resp.text
    # No side effects — the recipe list is unchanged and the name
    # can be reused.
    assert _recipe_count() == before
    assert _find_recipe_by_name(name) is None


def test__create_recipe__invalid_step_parent__rolls_back_the_whole_recipe(api):
    """A step whose parent_client_id doesn't match any sibling step is a
    step-shape ValueError inside `replace_steps_for_recipe`. The recipe +
    the sections that were queued earlier must all roll back — pre-FU-456
    those would have committed on their own before the steps insert
    tripped."""
    before = _recipe_count()
    name = f"FU-456 step probe {uuid4()}"
    resp = requests.post(RECIPES, json={
        "name": name,
        "sections": [
            {"client_id": "s1", "sequence": 0, "name": "Prep"},
        ],
        "steps": [
            {
                "client_id": "st1",
                "sequence": 0,
                "text": "Do the thing",
                # references a parent step that isn't in this write
                "parent_client_id": "no-such-parent",
            },
        ],
    })
    assert resp.status_code == 400, resp.text
    assert _recipe_count() == before
    assert _find_recipe_by_name(name) is None


def test__create_recipe__all_valid__commits_and_returns_the_id(api):
    """Golden path — one successful commit at the end."""
    before = _recipe_count()
    name = f"FU-456 happy path {uuid4()}"
    resp = requests.post(RECIPES, json={"name": name})
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body.get("recipe_id") or body.get("id"), body
    assert _recipe_count() == before + 1
    row = _find_recipe_by_name(name)
    assert row is not None
