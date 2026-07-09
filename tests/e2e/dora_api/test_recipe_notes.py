"""RD-29 (FU-432) — recipe personal notes round-trip.

`Recipe.notes` is a free-text field distinct from `instructions`; it's set on
create/update and surfaced in cook mode. This pins the create → read → clear
round-trip through the real endpoints.
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
RECIPES = f"{BASE}/recipes"


def _find(name: str):
    for r in requests.get(f"{RECIPES}?limit=500").json()["items"]:
        if r.get("name") == name:
            return r
    return None


def test__recipe_notes__create_read_update_clear(api):
    name = f"notes-probe-{uuid4()}"
    created = requests.post(RECIPES, json={
        "name": name,
        "notes": "I halve the chilli. Kids love it.",
    })
    assert created.status_code in (200, 201), created.text

    row = _find(name)
    assert row is not None
    assert row["notes"] == "I halve the chilli. Kids love it."
    recipe_id = row["recipe_id"]

    # Update the note.
    upd = requests.patch(f"{RECIPES}/{recipe_id}", json={"notes": "Now with extra garlic."})
    assert upd.status_code in (200, 204), upd.text
    assert _find(name)["notes"] == "Now with extra garlic."

    # Explicit null clears it.
    cleared = requests.patch(f"{RECIPES}/{recipe_id}", json={"notes": None})
    assert cleared.status_code in (200, 204), cleared.text
    assert _find(name)["notes"] is None


def test__recipe_notes__absent_defaults_to_null(api):
    name = f"notes-none-{uuid4()}"
    created = requests.post(RECIPES, json={"name": name})
    assert created.status_code in (200, 201), created.text
    assert _find(name)["notes"] is None
