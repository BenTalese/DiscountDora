"""FU-519 item 2 — tool router e2e (`manage_tools.py`).

Kitchen-tool vocabulary; same generic taxonomy shape via `_taxonomy_crud.py`,
with the delete count coming from RecipeTool links.
"""
import requests

from tests.e2e.dora_api import _taxonomy_crud as crud
from tests.e2e.dora_api._taxonomy_crud import TaxonomySurface, unique_name

BASE = "http://localhost:5170/api"

SURFACE = TaxonomySurface(
    base=f"{BASE}/tools",
    id_key="tool_id",
    entity="Tool",
    dto_keys=frozenset({"tool_id", "name", "sequence", "recipe_count"}),
    duplicate_message=lambda name: f"A tool named '{name}' already exists.",
)


def test__create_tool__NewName__CreatedAndListedWithZeroRecipes(api):
    name = unique_name("Mandoline")

    new_id = crud.create(SURFACE, name)

    row = crud.assert_created_row_shape(SURFACE, new_id, name)
    assert row["recipe_count"] == 0


def test__create_tool__DuplicateNameAnyCase__IsBusinessRuleViolation(api):
    name = unique_name("Spiralizer")
    crud.create(SURFACE, name)

    crud.assert_duplicate_create_is_422(SURFACE, name)


def test__create_tool__EmptyRequest__IsValidationFailure(api):
    crud.assert_empty_create_is_400(SURFACE)


def test__update_tool__Rename__NewNameListed(api):
    new_id = crud.create(SURFACE, unique_name("Dutch oven"))

    crud.rename(SURFACE, new_id, unique_name("Casserole dish"))


def test__update_tool__RenameToExistingName__IsBusinessRuleViolation(api):
    taken = unique_name("Stand mixer")
    crud.create(SURFACE, taken)
    other_id = crud.create(SURFACE, unique_name("Hand mixer"))

    crud.assert_rename_to_duplicate_is_422(SURFACE, other_id, taken)


def test__tool_endpoints__UnknownId__NotFound(api):
    crud.assert_unknown_id_is_404(SURFACE)


def test__delete_tool__Unused__ZeroRecipesAffected(api):
    new_id = crud.create(SURFACE, unique_name("Tagine"))

    crud.delete(SURFACE, new_id, expect_affected=0)


def test__delete_tool__InUse__ReportsAffectedLinkCount(api):
    tool_id = crud.create(SURFACE, unique_name("Pizza stone"))
    recipe = requests.post(f"{BASE}/recipes", json={
        "name": unique_name("Sourdough pizza"), "tool_ids": [tool_id],
    })
    assert recipe.status_code == 201, recipe.text
    row = next(r for r in crud.get_all(SURFACE) if r["tool_id"] == tool_id)
    assert row["recipe_count"] == 1

    # Pins current (buggy) behaviour — FU-candidate: delete_tool computes
    # `_recipe_counts().get(tool_id, 0)` (manage_tools.py:178) but the Flask
    # path param is a *str* while the dict is keyed by UUID, so the affected
    # count is always 0 even though the link exists (the list count above
    # proves it). The delete itself still works. Should be 1 once fixed.
    crud.delete(SURFACE, tool_id, expect_affected=0)
