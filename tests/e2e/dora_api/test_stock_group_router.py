"""FU-519 item 2 — stock group router e2e (`manage_stock_groups.py`).

Same generic taxonomy shape via `_taxonomy_crud.py`, with the stock-group
quirks pinned: no `sequence` (name-sorted), rename returns 204, delete
reports `items_affected` (stock items' group nulled via ON DELETE SET NULL).
"""
import requests

from tests.e2e.dora_api import _taxonomy_crud as crud
from tests.e2e.dora_api._taxonomy_crud import TaxonomySurface, unique_name
from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"

SURFACE = TaxonomySurface(
    base=f"{BASE}/stock-groups",
    id_key="stock_group_id",
    entity="StockGroup",
    dto_keys=frozenset({"stock_group_id", "name", "item_count"}),
    duplicate_message=lambda name: f"A stock group named '{name}' already exists.",
    update_status=204,
    delete_count_key="items_affected",
)


def test__create_stock_group__NewName__CreatedAndListedWithZeroItems(api):
    name = unique_name("Condiments")

    new_id = crud.create(SURFACE, name)

    row = crud.assert_created_row_shape(SURFACE, new_id, name)
    assert row["item_count"] == 0


def test__create_stock_group__DuplicateNameAnyCase__IsBusinessRuleViolation(api):
    name = unique_name("Tinned")
    crud.create(SURFACE, name)

    crud.assert_duplicate_create_is_422(SURFACE, name)


def test__create_stock_group__EmptyRequest__IsValidationFailure(api):
    crud.assert_empty_create_is_400(SURFACE)


def test__update_stock_group__Rename__NewNameListed(api):
    new_id = crud.create(SURFACE, unique_name("Frozen"))

    crud.rename(SURFACE, new_id, unique_name("Freezer staples"))


def test__update_stock_group__RenameToExistingName__IsBusinessRuleViolation(api):
    taken = unique_name("Dairy")
    crud.create(SURFACE, taken)
    other_id = crud.create(SURFACE, unique_name("Cheeses"))

    crud.assert_rename_to_duplicate_is_422(SURFACE, other_id, taken)


def test__stock_group_endpoints__UnknownId__NotFound(api):
    crud.assert_unknown_id_is_404(SURFACE)


def test__delete_stock_group__Unused__ZeroItemsAffected(api):
    new_id = crud.create(SURFACE, unique_name("Spices"))

    crud.delete(SURFACE, new_id, expect_affected=0)


def test__delete_stock_group__InUse__ReportsAffectedItemCount(api):
    group_id = crud.create(SURFACE, unique_name("Baking"))
    level = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
    item = make_stock_item(
        stock_level_id=level,
        name=unique_name("Vanilla paste"),
        stock_group_id=group_id,
    )
    row = next(r for r in crud.get_all(SURFACE) if r["stock_group_id"] == group_id)
    # Regression for the FU-527 fix (2026-07-12): GetStockGroupsHandler now
    # buckets via the underscore FK (`item._stock_group_id`) instead of the
    # lazy="noload" `item.stock_group` relationship, so item_count is real.
    assert row["item_count"] == 1

    crud.delete(SURFACE, group_id, expect_affected=1)

    # The FK nulls the item's group; the item itself survives.
    after = requests.get(
        f"{BASE}/stock-items",
        params={"filter": f"stock_item_id:eq:{item['stock_item_id']}"},
    ).json()["items"][0]
    assert after["stock_group_id"] is None
