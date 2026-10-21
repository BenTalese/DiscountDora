"""FU-519 item 2 — cuisine router e2e (`manage_cuisines.py`).

Generic taxonomy CRUD — contract legs live in `_taxonomy_crud.py`; this file
pins the cuisine-specific bits (DTO keys, duplicate copy, delete nulling
recipes' cuisine via ON DELETE SET NULL).
"""
import requests

from tests.e2e.dora_api import _taxonomy_crud as crud
from tests.e2e.dora_api._taxonomy_crud import TaxonomySurface, unique_name

BASE = "http://localhost:5170/api"

SURFACE = TaxonomySurface(
    base=f"{BASE}/cuisines",
    id_key="cuisine_id",
    entity="Cuisine",
    dto_keys=frozenset({"cuisine_id", "name", "sequence", "recipe_count"}),
    duplicate_message=lambda name: f"A cuisine named '{name}' already exists.",
)


def test__create_cuisine__NewName__CreatedAndListedWithZeroRecipes(api):
    name = unique_name("Cajun")

    new_id = crud.create(SURFACE, name)

    row = crud.assert_created_row_shape(SURFACE, new_id, name)
    assert row["recipe_count"] == 0


def test__create_cuisine__DuplicateNameAnyCase__IsBusinessRuleViolation(api):
    name = unique_name("Basque")
    crud.create(SURFACE, name)

    crud.assert_duplicate_create_is_422(SURFACE, name)


def test__create_cuisine__EmptyRequest__IsValidationFailure(api):
    crud.assert_empty_create_is_400(SURFACE)


def test__update_cuisine__Rename__NewNameListed(api):
    new_id = crud.create(SURFACE, unique_name("Tuscan"))

    crud.rename(SURFACE, new_id, unique_name("Umbrian"))


def test__update_cuisine__RenameToExistingName__IsBusinessRuleViolation(api):
    taken = unique_name("Persian")
    crud.create(SURFACE, taken)
    other_id = crud.create(SURFACE, unique_name("Levantine"))

    crud.assert_rename_to_duplicate_is_422(SURFACE, other_id, taken)


def test__cuisine_endpoints__UnknownId__NotFound(api):
    crud.assert_unknown_id_is_404(SURFACE)


def test__delete_cuisine__Unused__ZeroRecipesAffected(api):
    new_id = crud.create(SURFACE, unique_name("Breton"))

    crud.delete(SURFACE, new_id, expect_affected=0)


def test__delete_cuisine__InUse__ReportsAffectedRecipeCount(api):
    cuisine_id = crud.create(SURFACE, unique_name("Silesian"))
    recipe = requests.post(f"{BASE}/recipes", json={
        "name": unique_name("Pierogi"), "cuisine_id": cuisine_id,
    })
    assert recipe.status_code == 201, recipe.text
    row = next(r for r in crud.get_all(SURFACE) if r["cuisine_id"] == cuisine_id)
    assert row["recipe_count"] == 1

    crud.delete(SURFACE, cuisine_id, expect_affected=1)
