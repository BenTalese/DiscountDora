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


def test__recipe_notes__carry_onto_new_version(api):
    """DORA_VERIFY Cook-mode L305 — making a new version of a noted recipe
    carries the personal note onto the copy (`new_recipe_version.py:122`).
    A version that started life without a note stays note-free."""
    # Source with a note.
    name = f"notes-version-{uuid4()}"
    created = requests.post(RECIPES, json={
        "name": name,
        "notes": "Double the garlic; rest 10 min.",
    })
    assert created.status_code in (200, 201), created.text
    source_id = _find(name)["recipe_id"]

    resp = requests.post(f"{RECIPES}/{source_id}/new-version")
    assert resp.status_code in (200, 201), resp.text
    new_id = resp.json()["recipe_id"]
    assert new_id != source_id

    detail = requests.get(f"{RECIPES}/{new_id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["notes"] == "Double the garlic; rest 10 min."

    # A note-free source produces a note-free version (no phantom note).
    bare_name = f"notes-version-bare-{uuid4()}"
    bare = requests.post(RECIPES, json={"name": bare_name})
    assert bare.status_code in (200, 201), bare.text
    bare_id = _find(bare_name)["recipe_id"]
    bare_version = requests.post(f"{RECIPES}/{bare_id}/new-version")
    assert bare_version.status_code in (200, 201), bare_version.text
    bare_new_id = bare_version.json()["recipe_id"]
    assert requests.get(f"{RECIPES}/{bare_new_id}").json()["notes"] is None
