"""Owner-reported 2026-08-29 — "linking ingredients to step is broken (cannot
save)".

The recipe page sends `ingredients` on every PATCH (replace semantics) and
`steps` on every PATCH of a structured recipe, so a step that links an
ingredient sends both. `update_recipe` builds the replacement ingredient rows
in the ORM session and resolves the steps' `ingredient_client_ids` against
them — but the step access helper validates its link targets with a **Core**
`db.session.execute(select(table))`, which (unlike an ORM query) does not
autoflush. The new rows were therefore invisible to the check and every such
save 400'd with "Step references ingredients not on this recipe".

The contract pinned here is the round trip, not the internals: sending
ingredients and step links together persists the links against the ingredients
those links name. Worth an automated test rather than a manual re-walk (see
`DORA_VERIFY_TRIAGE.md`) — it is a backend invariant that holds across the
whole editor, and the failure mode is silent-until-you-hit-Save.
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
RECIPES = f"{BASE}/recipes"


def _detail(recipe_id: str) -> dict:
    resp = requests.get(f"{RECIPES}/{recipe_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


def _ingredients_payload(detail: dict) -> list[dict]:
    """The page's own shape: every row re-sent, keyed by the existing
    `recipe_ingredient_id` as its `client_id`."""
    return [
        {
            "stock_item_id": ing.get("stock_item_id"),
            "raw_text": ing.get("raw_text"),
            "quantity": ing.get("quantity"),
            "unit": ing.get("unit"),
            "notes": ing.get("notes"),
            "client_id": ing["recipe_ingredient_id"],
            "section_client_id": ing.get("section_id"),
            "is_optional": ing.get("is_optional", False),
        }
        for ing in detail["ingredients"]
    ]


def _make_recipe() -> dict:
    created = requests.post(RECIPES, json={
        "name": f"Step links {uuid4().hex[:8]}",
        "steps_mode": "structured",
        "ingredients": [
            {"raw_text": "sourdough", "quantity": 1, "unit": "loaf", "client_id": "i1"},
            {"raw_text": "butter", "quantity": 30, "unit": "g", "client_id": "i2"},
        ],
        "steps": [
            {"client_id": "s1", "sequence": 0, "text": "Slice the bread."},
        ],
    })
    assert created.status_code == 201, created.text
    return _detail(created.json()["recipe_id"])


def test__update_recipe__StepLinksAnIngredientBeingResent__SavesAndPersistsTheLink(api):
    detail = _make_recipe()
    bread, butter = (i["recipe_ingredient_id"] for i in detail["ingredients"])

    patched = requests.patch(f"{RECIPES}/{detail['recipe_id']}", json={
        "ingredients": _ingredients_payload(detail),
        "steps": [{
            "client_id": "s1",
            "sequence": 0,
            "text": "Slice the bread and butter it.",
            "ingredient_client_ids": [bread, butter],
        }],
    })
    assert patched.status_code == 204, patched.text

    # The ingredient rows are *replaced*, so the persisted link has to name the
    # new ids — not the ones the request sent. Assert by label, which survives
    # the re-key and is what the page actually renders.
    after = _detail(detail["recipe_id"])
    by_id = {i["recipe_ingredient_id"]: i["raw_text"] for i in after["ingredients"]}
    step = after["steps"][0]
    assert sorted(by_id[i] for i in step["ingredient_ids"]) == ["butter", "sourdough"]


def test__update_recipe__UnrelatedEditOnALinkedStep__StillSaves(api):
    """The owner hit this while changing an ingredient's unit, not while
    linking: the page re-sends the links untouched on every save, so a linked
    step made *every* subsequent edit unsaveable."""
    detail = _make_recipe()
    bread = detail["ingredients"][0]["recipe_ingredient_id"]

    linked = requests.patch(f"{RECIPES}/{detail['recipe_id']}", json={
        "ingredients": _ingredients_payload(detail),
        "steps": [{
            "client_id": "s1", "sequence": 0, "text": "Slice the bread.",
            "ingredient_client_ids": [bread],
        }],
    })
    assert linked.status_code == 204, linked.text

    # Second save: change the bread's unit, re-sending the step links verbatim.
    after = _detail(detail["recipe_id"])
    rows = _ingredients_payload(after)
    rows[0]["unit"] = "g"
    step = after["steps"][0]
    resaved = requests.patch(f"{RECIPES}/{detail['recipe_id']}", json={
        "ingredients": rows,
        "steps": [{
            "client_id": step["step_id"], "sequence": 0, "text": step["text"],
            "ingredient_client_ids": step["ingredient_ids"],
        }],
    })
    assert resaved.status_code == 204, resaved.text

    final = _detail(detail["recipe_id"])
    breads = [i for i in final["ingredients"] if i["raw_text"] == "sourdough"]
    assert breads[0]["unit"] == "g"
    assert len(final["steps"][0]["ingredient_ids"]) == 1
