"""Bigger-than-CRUD actions on shopping lists.

Bundled together because they share assumptions ("act on a list", "skip
ticked items where it matters", "pick a default merchant offer"). Splitting
each into its own file would just spread the same imports five ways.

Endpoints:

  POST /api/shopping-lists/<id>/move-unticked-to/<target_id>
      Move every unticked line from the source list onto a target list.
      The source list keeps its ticked lines. Duplicates on the target
      list are skipped (the per-list "unique stock item" invariant).

  POST /api/shopping-lists/<id>/refresh-deals
      Re-runs the cheapest-offer auto-pick for every line on the list,
      clearing any stale `selected_product_id` if a cheaper option now
      exists. Doesn't touch lines where the user has *explicitly* selected
      an offer that's still available.

  POST /api/shopping-lists/<id>/clear
      Deletes every line on the list. The list itself stays.

(X5 auto-generate moved to its own module — see auto_generate.py.)
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from dora_api.domain.entities.shopping_list import (ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation, ok,
                                                  no_content, not_found)
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# ───── Move unticked → existing list ──────────────────────────────────────

@dataclass(slots=True)
class MoveUntickedResponse:
    source_not_found: bool = False
    target_not_found: bool = False
    same_list: bool = False
    target_archived: bool = False
    moved_count: int = 0
    skipped_duplicates: int = 0


class MoveUntickedHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, source_id: UUID, target_id: UUID) -> MoveUntickedResponse:
        if source_id == target_id:
            return MoveUntickedResponse(same_list=True)

        source = self.repository.get(ShoppingList).by_id(source_id)
        if source is None:
            return MoveUntickedResponse(source_not_found=True)
        target = self.repository.get(ShoppingList).by_id(target_id)
        if target is None:
            return MoveUntickedResponse(target_not_found=True)
        if target.is_done:
            return MoveUntickedResponse(target_archived=True)

        unticked: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(source_id)
            & EntityField(ShoppingListLine, ShoppingListLine.Fields.IS_TICKED).eq(False)
        )
        target_lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(target_id)
        )
        target_item_ids = {l.stock_item_id for l in target_lines}
        next_sequence = (max((l.sequence for l in target_lines), default=-1)) + 1

        moved = 0
        skipped = 0
        for line in unticked:
            if line.stock_item_id in target_item_ids:
                # Don't merge quantities here — that's a separate UX
                # decision; the unique-per-line invariant wins for now.
                # Source line stays put.
                skipped += 1
                continue
            line.shopping_list_id = target_id
            line.sequence = next_sequence
            target_item_ids.add(line.stock_item_id)
            next_sequence += 1
            moved += 1

        self.repository.save_changes()
        return MoveUntickedResponse(moved_count=moved, skipped_duplicates=skipped)


@SHOPPING_LIST_ROUTER.route(
    "/<source_id>/move-unticked-to/<target_id>", methods=["POST"]
)
def move_unticked_to(source_id: UUID, target_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(MoveUntickedHandler).handle(source_id, target_id)
    if _Response.source_not_found:
        return not_found("ShoppingList (source)", source_id)
    if _Response.target_not_found:
        return not_found("ShoppingList (target)", target_id)
    if _Response.same_list:
        return business_rule_violation("Source and target lists are the same.")
    if _Response.target_archived:
        return business_rule_violation(
            "Cannot move items to an archived list. Unarchive it first."
        )
    _Logger.info(
        f"Moved {_Response.moved_count} unticked line(s) from {source_id} -> {target_id} "
        f"({_Response.skipped_duplicates} duplicates skipped)"
    )
    return ok({
        "moved_count": _Response.moved_count,
        "skipped_duplicates": _Response.skipped_duplicates,
    })


# ───── Refresh deals ──────────────────────────────────────────────────────

@dataclass(slots=True)
class RefreshDealsResponse:
    not_found: bool = False
    lines_checked: int = 0
    selections_cleared: int = 0


class RefreshDealsHandler:
    """Cleans up stale `selected_product_id` values.

    Background: when a user picks a specific merchant offer, that selection
    can go stale (the product gets unlinked, the merchant disappears, etc).
    Rather than pull fresh prices on demand (we'd need to hit the merchant
    API per product), we lean on the existing scraping pipeline and just
    re-validate each line's selection here:

      - If the selected product is still linked to the stock item: keep.
      - Otherwise: clear the selection so the line falls back to "cheapest
        currently linked".

    A future iteration could trigger a fresh scrape per product, but that
    crosses into merchant_api territory and is out of scope right now.
    """

    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, shopping_list_id: UUID) -> RefreshDealsResponse:
        lst = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return RefreshDealsResponse(not_found=True)

        lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
        )
        if not lines:
            return RefreshDealsResponse(lines_checked=0)

        stock_item_ids = list({l.stock_item_id for l in lines})
        items: List[StockItem] = (
            self.repository.get(StockItem)
            .include(StockItem.Fields.PRODUCTS)
            .all(EntityField(StockItem, "id").in_(stock_item_ids))
        )
        items_by_id = {i.id: i for i in items}

        cleared = 0
        for line in lines:
            if line.selected_product_id is None:
                continue
            item = items_by_id.get(line.stock_item_id)
            still_linked = bool(
                item
                and any(p.id == line.selected_product_id for p in (item.products or []))
            )
            if not still_linked:
                line.selected_product_id = None
                cleared += 1

        self.repository.save_changes()
        return RefreshDealsResponse(
            lines_checked=len(lines), selections_cleared=cleared
        )


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/refresh-deals", methods=["POST"])
def refresh_deals(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(RefreshDealsHandler).handle(shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(
        f"Refreshed deals on list {shopping_list_id}: "
        f"checked {_Response.lines_checked}, cleared {_Response.selections_cleared}"
    )
    return ok({
        "lines_checked": _Response.lines_checked,
        "selections_cleared": _Response.selections_cleared,
    })


# ───── Clear all lines ────────────────────────────────────────────────────

@dataclass(slots=True)
class ClearListResponse:
    not_found: bool = False
    removed_count: int = 0


class ClearListHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, shopping_list_id: UUID) -> ClearListResponse:
        lst = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return ClearListResponse(not_found=True)
        lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
        )
        for line in lines:
            self.repository.remove(line)
        self.repository.save_changes()
        return ClearListResponse(removed_count=len(lines))


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/clear", methods=["POST"])
def clear_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(ClearListHandler).handle(shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(f"Cleared {_Response.removed_count} lines from list {shopping_list_id}")
    return ok({"removed_count": _Response.removed_count})
