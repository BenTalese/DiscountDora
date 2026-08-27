"""Recipe-view feedback 2026-08-27 — a structured recipe's tools are derived.

The owner's call: in `structured` mode the recipe's tool set is the union of
what its steps declare, and there is no second place to type it. The
recipe-level `RecipeTool` rows still exist because that is what the cookbook's
tool filter reads — so the derivation has to run on *every* write that can
change it, or the filter quietly drifts away from the steps.

Freeform and photo recipes have no steps to derive from and keep the manual
field, which is the other half of the contract pinned here.
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
RECIPES = f"{BASE}/recipes"
TOOLS = f"{BASE}/tools"


def _make_tool(prefix: str) -> str:
    resp = requests.post(TOOLS, json={"name": f"{prefix} {uuid4().hex[:8]}"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return body.get("tool_id") or body["id"]


def _detail(recipe_id: str) -> dict:
    resp = requests.get(f"{RECIPES}/{recipe_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


def test__create_recipe__StructuredStepsCarryTools__RecipeToolsAreTheirUnion(api):
    whisk = _make_tool("Derivation Whisk")
    pan = _make_tool("Derivation Pan")

    resp = requests.post(RECIPES, json={
        "name": f"Derived Tools Create {uuid4().hex[:8]}",
        "steps_mode": "structured",
        "steps": [
            {"client_id": "s1", "sequence": 0, "text": "Whisk it.", "tool_ids": [whisk]},
            {"client_id": "s2", "sequence": 1, "text": "Fry it.", "tool_ids": [pan, whisk]},
        ],
    })
    assert resp.status_code == 201, resp.text

    # Union, deduped — `whisk` appears on both steps and once on the recipe.
    detail = _detail(resp.json()["recipe_id"])
    assert sorted(detail["tool_ids"]) == sorted([whisk, pan])


def test__update_recipe__StepToolsChange__RecipeToolsFollowAndDropTheOldOnes(api):
    whisk = _make_tool("Derivation Follow Whisk")
    pan = _make_tool("Derivation Follow Pan")

    created = requests.post(RECIPES, json={
        "name": f"Derived Tools Update {uuid4().hex[:8]}",
        "steps_mode": "structured",
        "steps": [{"client_id": "s1", "sequence": 0, "text": "Whisk it.", "tool_ids": [whisk]}],
    })
    assert created.status_code == 201, created.text
    recipe_id = created.json()["recipe_id"]

    # Rewrite the steps so the only tool used is now the pan. The whisk has to
    # leave the recipe with it — a derived set that only ever grows would make
    # the cookbook filter return recipes that no longer use the tool.
    patched = requests.patch(f"{RECIPES}/{recipe_id}", json={
        "steps": [{"client_id": "s1", "sequence": 0, "text": "Fry it.", "tool_ids": [pan]}],
    })
    assert patched.status_code == 204, patched.text

    assert _detail(recipe_id)["tool_ids"] == [pan]


def test__update_recipe__StructuredWithClientSentTools__DerivationWins(api):
    """An older client (or the importer) may still send a recipe-level
    `tool_ids`. On a structured recipe that list is not the truth, so it is
    overwritten rather than rejected — a 400 would break a caller that has
    done nothing wrong."""
    step_tool = _make_tool("Derivation Wins Step")
    typed_tool = _make_tool("Derivation Wins Typed")

    created = requests.post(RECIPES, json={
        "name": f"Derived Tools Wins {uuid4().hex[:8]}",
        "steps_mode": "structured",
        "steps": [{"client_id": "s1", "sequence": 0, "text": "Do it.", "tool_ids": [step_tool]}],
    })
    assert created.status_code == 201, created.text
    recipe_id = created.json()["recipe_id"]

    patched = requests.patch(f"{RECIPES}/{recipe_id}", json={
        "tool_ids": [typed_tool],
        "steps": [{"client_id": "s1", "sequence": 0, "text": "Do it.", "tool_ids": [step_tool]}],
    })
    assert patched.status_code == 204, patched.text

    assert _detail(recipe_id)["tool_ids"] == [step_tool]


def test__update_recipe__FreeformMode__KeepsTheToolsYouTyped(api):
    """The other half of the rule: with no steps to derive from, the field is
    real. This is what the method section renders for free-text and photo
    recipes, and it must survive a PATCH untouched."""
    typed_tool = _make_tool("Derivation Freeform")

    created = requests.post(RECIPES, json={
        "name": f"Derived Tools Freeform {uuid4().hex[:8]}",
        "steps_mode": "freeform",
        "instructions": "Mix.\nBake.",
    })
    assert created.status_code == 201, created.text
    recipe_id = created.json()["recipe_id"]

    patched = requests.patch(f"{RECIPES}/{recipe_id}", json={"tool_ids": [typed_tool]})
    assert patched.status_code == 204, patched.text

    assert _detail(recipe_id)["tool_ids"] == [typed_tool]


def test__update_recipe__FlipToStructured__PicksUpTheToolsItsStepsAlreadyDeclare(api):
    """The mode flip is the case the derivation would miss if it only ran
    alongside a `steps` replace: the steps are already there, the payload only
    changes `steps_mode`, and the recipe-level set has to catch up."""
    step_tool = _make_tool("Derivation Flip Step")
    typed_tool = _make_tool("Derivation Flip Typed")

    created = requests.post(RECIPES, json={
        "name": f"Derived Tools Flip {uuid4().hex[:8]}",
        "steps_mode": "freeform",
        "instructions": "Mix.",
        "tool_ids": [typed_tool],
        "steps": [{"client_id": "s1", "sequence": 0, "text": "Mix it.", "tool_ids": [step_tool]}],
    })
    assert created.status_code == 201, created.text
    recipe_id = created.json()["recipe_id"]
    assert _detail(recipe_id)["tool_ids"] == [typed_tool]

    patched = requests.patch(f"{RECIPES}/{recipe_id}", json={"steps_mode": "structured"})
    assert patched.status_code == 204, patched.text

    assert _detail(recipe_id)["tool_ids"] == [step_tool]
