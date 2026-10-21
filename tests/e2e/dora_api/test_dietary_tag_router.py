"""FU-519 item 2 — dietary tag router e2e (`manage_dietary_tags.py`).

Same generic taxonomy shape via `_taxonomy_crud.py`, plus the tag-specific
`category` field (create requires it; PATCH can recategorise) and the
delete count coming from RecipeTag links (ON DELETE CASCADE).
"""
import requests

from tests.e2e.dora_api import _taxonomy_crud as crud
from tests.e2e.dora_api._taxonomy_crud import TaxonomySurface, unique_name
from tests.support import assert_problem

BASE = "http://localhost:5170/api"

SURFACE = TaxonomySurface(
    base=f"{BASE}/dietary-tags",
    id_key="dietary_tag_id",
    entity="DietaryTag",
    dto_keys=frozenset({"dietary_tag_id", "name", "category", "sequence", "recipe_count"}),
    duplicate_message=lambda name: f"A dietary tag named '{name}' already exists.",
    create_body=lambda name: {"name": name, "category": "Lifestyle"},
)


def test__create_dietary_tag__NewName__CreatedWithCategoryAndZeroRecipes(api):
    name = unique_name("Pescatarian")

    new_id = crud.create(SURFACE, name)

    row = crud.assert_created_row_shape(SURFACE, new_id, name)
    assert row["category"] == "Lifestyle"
    assert row["recipe_count"] == 0


def test__create_dietary_tag__DuplicateNameAnyCase__IsBusinessRuleViolation(api):
    name = unique_name("Flexitarian")
    crud.create(SURFACE, name)

    crud.assert_duplicate_create_is_422(SURFACE, name)


def test__create_dietary_tag__MissingCategory__IsValidationFailure(api):
    resp = requests.post(SURFACE.base, json={"name": unique_name("Halal")})

    assert_problem(resp, 400, field="category", title="Malformed request.")


def test__update_dietary_tag__RenameAndRecategorise__BothApplied(api):
    new_id = crud.create(SURFACE, unique_name("Low FODMAP"))
    new_name = unique_name("Low-FODMAP")

    resp = requests.patch(
        f"{SURFACE.base}/{new_id}",
        json={"name": new_name, "category": "Medical"},
    )

    assert resp.status_code == 200, resp.text
    row = next(r for r in crud.get_all(SURFACE) if r["dietary_tag_id"] == new_id)
    assert row["name"] == new_name
    assert row["category"] == "Medical"


def test__update_dietary_tag__RenameToExistingName__IsBusinessRuleViolation(api):
    taken = unique_name("Kosher")
    crud.create(SURFACE, taken)
    other_id = crud.create(SURFACE, unique_name("Teetotal"))

    crud.assert_rename_to_duplicate_is_422(SURFACE, other_id, taken)


def test__dietary_tag_endpoints__UnknownId__NotFound(api):
    crud.assert_unknown_id_is_404(SURFACE)


def test__delete_dietary_tag__Unused__ZeroRecipesAffected(api):
    new_id = crud.create(SURFACE, unique_name("Raw"))

    crud.delete(SURFACE, new_id, expect_affected=0)


def test__delete_dietary_tag__InUse__ReportsAffectedLinkCount(api):
    tag_id = crud.create(SURFACE, unique_name("Nut-free"))
    recipe = requests.post(f"{BASE}/recipes", json={
        "name": unique_name("Nutless brownie"), "dietary_tag_ids": [tag_id],
    })
    assert recipe.status_code == 201, recipe.text
    row = next(r for r in crud.get_all(SURFACE) if r["dietary_tag_id"] == tag_id)
    assert row["recipe_count"] == 1

    # Regression for the FU-528 fix (2026-07-12): the handler coerces the str
    # path param to UUID before the UUID-keyed `_recipe_counts()` lookup, so
    # recipes_affected reports the real count instead of always 0.
    crud.delete(SURFACE, tag_id, expect_affected=1)
