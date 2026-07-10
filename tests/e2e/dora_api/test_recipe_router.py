"""FU-519 / PROPOSAL_TEST_SUITE_IMPROVEMENTS §5.D — recipe router e2e coverage.

CRUD round-trips, list filters (cookability axes, ingredient_exclude,
expiring_within_days), cookability fields on list + detail DTOs, and the
key 400/404/422 error paths. Complements (does not duplicate) the
existing pinned suites: test_recipes_query_count.py,
test_recipe_is_planned.py, test_recipe_notes.py,
test_create_recipe_unit_of_work.py, test_new_recipe_version_unit_of_work.py.

Determinism: any date used (expiry windows) is derived from the single
household-today anchor exposed by GET /api/meal-plans/today — never from
a local wall-clock read (see the 2026-07-10 timezone-flake rule).
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
import requests

from tests.e2e.dora_api._error_assertions import domain_err, validation_err
from tests.factories import make_stock_item
from tests.support import assert_envelope, assert_problem, is_valid_uuid

BASE = "http://localhost:5170/api"
RECIPES = f"{BASE}/recipes"

# Cookability contract fields every list/detail DTO must carry
# (state-ownership §3.2 + IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 tri-state).
COOKABILITY_KEYS = {
    "cookable",
    "missing_count",
    "missing_stock_item_names",
    "unlinked_ingredient_count",
}

# Identity / core fields the cookbook list render depends on. A subset
# check (not full-set equality) so additive DTO growth doesn't break this
# suite; the cookability contract above is the part we pin hard.
LIST_DTO_CORE_KEYS = {
    "recipe_id",
    "name",
    "available_meals",
    "unallocated_meals",
    "committed_meals",
    "is_planned",
    "is_favourite",
    "ingredients",
    "has_image",
    "created_at",
    "servings",
    "kcal",
    "notes",
} | COOKABILITY_KEYS

#region ---------------- setup ----------------


def _stock_level_id(sequence: int) -> str:
    """Resolve a stock-level id by its canonical status sequence
    (0 Stocked / 1 Low / 2 Out — see dora_api.domain.stock_status)."""
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == sequence)


def _make_item(name_prefix: str, sequence: int, **overrides) -> dict:
    """Create a stock item at the given stock-status sequence with a
    collision-proof name. Returns the created DTO."""
    return make_stock_item(
        stock_level_id=_stock_level_id(sequence),
        name=f"{name_prefix} {uuid4().hex[:8]}",
        **overrides,
    )


def _make_recipe(name_prefix: str = "E2E Recipe", **body) -> dict:
    """Create a recipe via POST /api/recipes and return the echoed detail
    DTO. Name is collision-proof unless the caller pins one."""
    payload = {"name": f"{name_prefix} {uuid4().hex[:8]}", **body}
    resp = requests.post(RECIPES, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _list_items(query: str = "") -> list:
    return assert_envelope(requests.get(f"{RECIPES}{query}"))


def _by_id(recipe_id: str) -> dict | None:
    items = _list_items(f"?filter=recipe_id:eq:{recipe_id}")
    return items[0] if items else None


def _household_today() -> date:
    return date.fromisoformat(
        requests.get(f"{BASE}/meal-plans/today").json()["today"]
    )

#endregion setup

#region ---------------- create ----------------


def test__create_recipe__AllCoreAttributes__RecipeCreatedAndDetailDtoEchoed(api):
    _Item = _make_item("Recipe Router Flour", 0)
    _Name = f"Router Full Recipe {uuid4().hex[:8]}"

    _Response = requests.post(RECIPES, json={
        "name": _Name,
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 25,
        "kcal": 650,
        "difficulty": "Easy",
        "instructions": "Mix.\nBake.",
        "notes": "Family favourite.",
        "ingredients": [
            {"stock_item_id": _Item["stock_item_id"], "quantity": 2, "unit": "cup"},
        ],
    })

    assert _Response.status_code == 201, _Response.text
    assert _Response.headers["Content-Type"] == "application/json"
    assert f"/api/recipes?filter=recipe_id:eq:" in _Response.headers["location"]
    _Body = _Response.json()
    assert is_valid_uuid(_Body["recipe_id"])
    assert _Body["name"] == _Name
    assert _Body["servings"] == 4
    assert _Body["prep_time_minutes"] == 10
    assert _Body["cook_time_minutes"] == 25
    assert _Body["kcal"] == 650
    assert _Body["difficulty"] == "Easy"
    assert _Body["notes"] == "Family favourite."
    assert len(_Body["ingredients"]) == 1
    assert _Body["ingredients"][0]["stock_item_id"] == _Item["stock_item_id"]
    assert _Body["ingredients"][0]["quantity"] == 2
    assert _Body["ingredients"][0]["unit"] == "cup"


def test__create_recipe__EmptyRequest__IsRequiredInputsValidationFailure(api):
    _Response = requests.post(RECIPES, json={})

    assert_problem(_Response, 400, title="Malformed request.")
    assert _Response.json()["errors"] == {
        "name": [validation_err("missing", "Field required")],
    }


def test__create_recipe__DuplicateName__IsBusinessRuleViolation(api):
    _Name = f"Router Duplicate Recipe {uuid4().hex[:8]}"
    assert requests.post(RECIPES, json={"name": _Name}).status_code == 201

    _Response = requests.post(RECIPES, json={"name": _Name})

    _Body = assert_problem(_Response, 422, title="Business rule violation.")
    assert _Body["errors"] == {
        "": [domain_err(f"A recipe with the name '{_Name}' already exists.")],
    }


def test__create_recipe__UnknownStockItemInIngredients__IsEntityExistenceFailure(api):
    _FakeID = uuid4()

    _Response = requests.post(RECIPES, json={
        "name": f"Router Ghost Ingredient {uuid4().hex[:8]}",
        "ingredients": [{"stock_item_id": str(_FakeID)}],
    })

    _Body = assert_problem(_Response, 422, field="ingredients")
    assert _Body["errors"]["ingredients"] == [
        domain_err(f"StockItem(s) with the ID(s) '{_FakeID}' were not found."),
    ]


def test__create_recipe__UnknownCuisine__IsEntityExistenceFailure(api):
    _FakeID = uuid4()

    _Response = requests.post(RECIPES, json={
        "name": f"Router Ghost Cuisine {uuid4().hex[:8]}",
        "cuisine_id": str(_FakeID),
    })

    _Body = assert_problem(_Response, 422, field="cuisine_id", title="Entity was not found.")
    assert _Body["errors"]["cuisine_id"] == [
        domain_err(f"Cuisine with the ID '{_FakeID}' was not found."),
    ]


def test__create_recipe__InvalidDifficulty__IsBadRequest(api):
    _Response = requests.post(RECIPES, json={
        "name": f"Router Bad Difficulty {uuid4().hex[:8]}",
        "difficulty": "impossible",
    })

    _Body = assert_problem(_Response, 400)
    assert "Invalid difficulty 'impossible'" in _Body["title"]


def test__create_recipe__IngredientWithNoStockItemAndNoRawText__IsValidationFailure(api):
    # Chunk 4 invariant: every ingredient row needs an anchor — a linked
    # stock_item_id or non-blank raw_text.
    _Response = requests.post(RECIPES, json={
        "name": f"Router Anchorless Ingredient {uuid4().hex[:8]}",
        "ingredients": [{"quantity": 1}],
    })

    assert_problem(_Response, 400, title="Malformed request.")


def test__create_recipe__ExtraAttributes__IsBadRequest(api):
    _Response = requests.post(RECIPES, json={
        "name": f"Router Extra Attr {uuid4().hex[:8]}",
        "poopusgoopus": "aaaa",
    })

    _Body = assert_problem(_Response, 400, field="poopusgoopus")
    assert _Body["errors"]["poopusgoopus"] == [
        validation_err("extra_forbidden", "Extra inputs are not permitted"),
    ]

#endregion create

#region ---------------- read: detail + list shape ----------------


def test__get_recipe__ById__ReturnsFullDetailDto(api):
    _Created = _make_recipe("Router Detail Read", instructions="Step one.")

    _Response = requests.get(f"{RECIPES}/{_Created['recipe_id']}")

    assert _Response.status_code == 200
    _Detail = _Response.json()
    assert _Detail["recipe_id"] == _Created["recipe_id"]
    assert _Detail["name"] == _Created["name"]
    # Detail-only surfaces must exist (lists may be empty).
    assert isinstance(_Detail["steps"], list)
    assert isinstance(_Detail["sections"], list)
    assert isinstance(_Detail["version_siblings"], list)
    assert isinstance(_Detail["step_images"], list)
    assert "estimated_cost" in _Detail
    assert COOKABILITY_KEYS <= _Detail.keys()


def test__get_recipe__DoesNotExist__RecipeNotFound(api):
    _FakeID = uuid4()

    _Response = requests.get(f"{RECIPES}/{_FakeID}")

    _Body = assert_problem(_Response, 404, title="Entity was not found.")
    assert _Body["detail"] == f"Recipe with the ID '{_FakeID}' was not found."


def test__get_recipes__ListDto__CarriesCoreAndCookabilityKeys(api):
    _Created = _make_recipe("Router List Shape")

    _Row = _by_id(_Created["recipe_id"])

    assert _Row is not None
    assert LIST_DTO_CORE_KEYS <= _Row.keys()


def test__get_recipes__FilterByIdForUnknownRecipe__EmptyResult(api):
    _Response = requests.get(f"{RECIPES}?filter=recipe_id:eq:{uuid4()}")

    assert_envelope(_Response, expect_total=0)


def test__get_recipes__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f"{RECIPES}?filter=poopusgoopus:eq:1")

    _Body = assert_problem(_Response, 400)
    assert _Body["title"] == "Field 'poopusgoopus' is not filterable on 'Recipe'."


# FU-169 Phase 2 reference shape — parametrized pagination-validation matrix.
@pytest.mark.parametrize(
    "query,invalid_field",
    [
        ("page=true&limit=2", "page"),
        ("page=1&limit=true", "limit"),
    ],
    ids=["page-is-not-integer", "limit-is-not-integer"],
)
def test__get_recipes__pagination_value_is_not_integer__IsBadRequest(api, query, invalid_field):
    _Response = requests.get(f"{RECIPES}?{query}")

    assert_problem(_Response, 400)
    assert _Response.json() == {
        "detail": "See errors property for more details.",
        "errors": {},
        "status": 400,
        "title": f"'{invalid_field}' must be an integer.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1",
    }


def test__get_recipes__PagingWithLimit__RespectsPageSize(api):
    for _i in range(3):
        _make_recipe("Router Page Probe")

    _Response = requests.get(f"{RECIPES}?page=1&limit=2")

    assert _Response.status_code == 200
    _Body = _Response.json()
    assert _Body["page"] == 1
    assert _Body["limit"] == 2
    assert len(_Body["items"]) == 2
    assert _Body["total"] >= 3

#endregion read

#region ---------------- cookability surfacing + filters ----------------


def test__get_recipes__AllIngredientsStocked__CookableTrueWithNothingMissing(api):
    _Item = _make_item("Cookable Stocked", 0)
    _Created = _make_recipe("Router Cookable", ingredients=[
        {"stock_item_id": _Item["stock_item_id"]},
    ])

    _Row = _by_id(_Created["recipe_id"])

    assert _Row["cookable"] is True
    assert _Row["missing_count"] == 0
    assert _Row["missing_stock_item_names"] == []
    assert _Row["unlinked_ingredient_count"] == 0


def test__get_recipes__OutOfStockIngredient__CookableFalseAndMissingNamed(api):
    _Item = _make_item("Cookable OutOfStock", 2)
    _Created = _make_recipe("Router Uncookable", ingredients=[
        {"stock_item_id": _Item["stock_item_id"]},
    ])

    _Row = _by_id(_Created["recipe_id"])

    assert _Row["cookable"] is False
    assert _Row["missing_count"] == 1
    assert _Row["missing_stock_item_names"] == [_Item["name"]]
    # Ingredient-level status flags mirror the server-owned rule (§3.1).
    assert _Row["ingredients"][0]["is_missing"] is True


def test__get_recipes__UnlinkedRequiredIngredient__CookableIsTriStateNull(api):
    # IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — raw_text-only rows make
    # cookability unknown, not false.
    _Created = _make_recipe("Router Unlinked", ingredients=[
        {"raw_text": "1 pound ground turkey"},
    ])

    _Row = _by_id(_Created["recipe_id"])

    assert _Row["cookable"] is None
    assert _Row["unlinked_ingredient_count"] == 1
    assert _Row["missing_count"] == 0
    assert _Row["ingredients"][0]["stock_item_id"] is None
    assert _Row["ingredients"][0]["raw_text"] == "1 pound ground turkey"


def test__get_recipes__OptionalMissingIngredient__DoesNotBlockCookable(api):
    # Cookbook revision §1.9 — optional rows are ignored by the rollup.
    _Stocked = _make_item("Optional Stocked", 0)
    _Out = _make_item("Optional OutOfStock", 2)
    _Created = _make_recipe("Router Optional", ingredients=[
        {"stock_item_id": _Stocked["stock_item_id"]},
        {"stock_item_id": _Out["stock_item_id"], "is_optional": True},
    ])

    _Row = _by_id(_Created["recipe_id"])

    assert _Row["cookable"] is True
    assert _Row["missing_count"] == 0
    assert _Row["missing_stock_item_names"] == []


def test__get_recipes__CookableTrueFilter__KeepsCookableExcludesFalseAndUnknown(api):
    _Stocked = _make_item("Filter Stocked", 0)
    _Out = _make_item("Filter OutOfStock", 2)
    _CookableId = _make_recipe("Filter Cookable", ingredients=[
        {"stock_item_id": _Stocked["stock_item_id"]},
    ])["recipe_id"]
    _UncookableId = _make_recipe("Filter Uncookable", ingredients=[
        {"stock_item_id": _Out["stock_item_id"]},
    ])["recipe_id"]
    _UnknownId = _make_recipe("Filter Unknown", ingredients=[
        {"raw_text": "mystery spice"},
    ])["recipe_id"]

    _Ids = {r["recipe_id"] for r in _list_items("?cookable=true&limit=500")}

    assert _CookableId in _Ids
    assert _UncookableId not in _Ids
    # Tri-state None is excluded from BOTH cookable axes.
    assert _UnknownId not in _Ids


def test__get_recipes__CookableFalseFilter__KeepsOnlyDefinitelyUncookable(api):
    _Stocked = _make_item("FilterF Stocked", 0)
    _Out = _make_item("FilterF OutOfStock", 2)
    _CookableId = _make_recipe("FilterF Cookable", ingredients=[
        {"stock_item_id": _Stocked["stock_item_id"]},
    ])["recipe_id"]
    _UncookableId = _make_recipe("FilterF Uncookable", ingredients=[
        {"stock_item_id": _Out["stock_item_id"]},
    ])["recipe_id"]
    _UnknownId = _make_recipe("FilterF Unknown", ingredients=[
        {"raw_text": "mystery spice"},
    ])["recipe_id"]

    _Ids = {r["recipe_id"] for r in _list_items("?cookable=false&limit=500")}

    assert _UncookableId in _Ids
    assert _CookableId not in _Ids
    assert _UnknownId not in _Ids


def test__get_recipes__MaxMissingFilter__ExcludesRecipesOverThreshold(api):
    _OutA = _make_item("MaxMissing A", 2)
    _OutB = _make_item("MaxMissing B", 2)
    _OneMissingId = _make_recipe("MaxMissing One", ingredients=[
        {"stock_item_id": _OutA["stock_item_id"]},
    ])["recipe_id"]
    _TwoMissingId = _make_recipe("MaxMissing Two", ingredients=[
        {"stock_item_id": _OutA["stock_item_id"]},
        {"stock_item_id": _OutB["stock_item_id"]},
    ])["recipe_id"]

    _Ids = {r["recipe_id"] for r in _list_items("?max_missing=1&limit=500")}

    assert _OneMissingId in _Ids
    assert _TwoMissingId not in _Ids


def test__get_recipes__IngredientExcludeFilter__DropsRecipesUsingTheIngredient(api):
    _Token = uuid4().hex[:8]
    _Egg = make_stock_item(
        stock_level_id=_stock_level_id(0),
        name=f"Excludable Egg {_Token}",
    )
    _Safe = _make_item("Exclude Safe", 0)
    _WithEggId = _make_recipe("Exclude WithEgg", ingredients=[
        {"stock_item_id": _Egg["stock_item_id"]},
    ])["recipe_id"]
    _WithoutEggId = _make_recipe("Exclude WithoutEgg", ingredients=[
        {"stock_item_id": _Safe["stock_item_id"]},
    ])["recipe_id"]

    _Ids = {
        r["recipe_id"]
        for r in _list_items(f"?ingredient_exclude=excludable egg {_Token}&limit=500")
    }

    assert _WithEggId not in _Ids
    assert _WithoutEggId in _Ids


def test__get_recipes__ExpiringWithinDaysFilter__KeepsRecipesUsingAtRiskStock(api):
    # C-waste W4 — both the restriction and the per-recipe count. Dates are
    # relative to the single household-today anchor (determinism rule).
    _Today = _household_today()
    _Expiring = make_stock_item(
        stock_level_id=_stock_level_id(0),
        name=f"Expiring Soon Cream {uuid4().hex[:8]}",
        expiry_date=(_Today + timedelta(days=3)).isoformat(),
    )
    _Stable = _make_item("Never Expires", 0)
    _UsesExpiringId = _make_recipe("Expiring User", ingredients=[
        {"stock_item_id": _Expiring["stock_item_id"]},
    ])["recipe_id"]
    _StableOnlyId = _make_recipe("Expiring NonUser", ingredients=[
        {"stock_item_id": _Stable["stock_item_id"]},
    ])["recipe_id"]

    _Rows = _list_items("?expiring_within_days=7&limit=500")
    _ById = {r["recipe_id"]: r for r in _Rows}

    assert _UsesExpiringId in _ById
    assert _ById[_UsesExpiringId]["expiring_ingredient_count"] == 1
    assert _StableOnlyId not in _ById

#endregion cookability

#region ---------------- update ----------------


def test__update_recipe__RenameOnly__OnlyNameChanges(api):
    _Created = _make_recipe("Router Rename", servings=3)
    _NewName = f"Router Renamed {uuid4().hex[:8]}"

    _PatchResponse = requests.patch(
        f"{RECIPES}/{_Created['recipe_id']}", json={"name": _NewName},
    )
    _After = _by_id(_Created["recipe_id"])

    assert _PatchResponse.status_code == 204
    assert _After["name"] == _NewName
    assert _After["servings"] == 3


def test__update_recipe__TogglingFavourite__FavouritePersisted(api):
    _Created = _make_recipe("Router Favourite")
    assert _Created["is_favourite"] is False

    _PatchResponse = requests.patch(
        f"{RECIPES}/{_Created['recipe_id']}", json={"is_favourite": True},
    )

    assert _PatchResponse.status_code == 204
    assert _by_id(_Created["recipe_id"])["is_favourite"] is True


def test__update_recipe__ReplacingIngredients__IngredientSetReplaced(api):
    _First = _make_item("Update Ing First", 0)
    _Second = _make_item("Update Ing Second", 0)
    _Created = _make_recipe("Router ReplaceIngredients", ingredients=[
        {"stock_item_id": _First["stock_item_id"]},
    ])

    _PatchResponse = requests.patch(
        f"{RECIPES}/{_Created['recipe_id']}",
        json={"ingredients": [
            {"stock_item_id": _Second["stock_item_id"], "quantity": 5, "unit": "g"},
        ]},
    )
    _After = _by_id(_Created["recipe_id"])

    assert _PatchResponse.status_code == 204
    assert len(_After["ingredients"]) == 1
    assert _After["ingredients"][0]["stock_item_id"] == _Second["stock_item_id"]
    assert _After["ingredients"][0]["quantity"] == 5


def test__update_recipe__OtherRecipeHasSameName__CannotUpdateToDuplicateName(api):
    _Existing = _make_recipe("Router Name Holder")
    _Victim = _make_recipe("Router Name Wanter")

    _PatchResponse = requests.patch(
        f"{RECIPES}/{_Victim['recipe_id']}", json={"name": _Existing["name"]},
    )

    _Body = assert_problem(_PatchResponse, 422, title="Business rule violation.")
    assert _Body["errors"] == {
        "": [domain_err(f"A recipe with the name '{_Existing['name']}' already exists.")],
    }


def test__update_recipe__RecipeDoesNotExist__RecipeNotFound(api):
    _FakeID = uuid4()

    _Response = requests.patch(f"{RECIPES}/{_FakeID}", json={})

    _Body = assert_problem(_Response, 404, title="Entity was not found.")
    assert _Body["detail"] == f"Recipe with the ID '{_FakeID}' was not found."

#endregion update

#region ---------------- delete ----------------


def test__delete_recipe__DeletingRecipe__RecipeGoneFromListAndDetail(api):
    _Created = _make_recipe("Router Delete Me")

    _DeleteResponse = requests.delete(f"{RECIPES}/{_Created['recipe_id']}")

    assert _DeleteResponse.status_code == 204
    assert _by_id(_Created["recipe_id"]) is None
    assert requests.get(f"{RECIPES}/{_Created['recipe_id']}").status_code == 404


def test__delete_recipe__RecipeDoesNotExist__RecipeNotFound(api):
    _FakeID = uuid4()

    _Response = requests.delete(f"{RECIPES}/{_FakeID}")

    _Body = assert_problem(_Response, 404, title="Entity was not found.")
    assert _Body["detail"] == f"Recipe with the ID '{_FakeID}' was not found."

#endregion delete
