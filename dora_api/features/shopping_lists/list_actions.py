"""Bigger-than-CRUD actions on shopping lists.

Bundled together because they share assumptions ("act on a list", "skip
ticked items where it matters", "pick a default merchant offer"). Splitting
each into its own file would just spread the same imports five ways.

Endpoints:

  POST /api/shopping-lists/<id>/move-unticked-to/<target_id>
      Move every unticked line from the source list onto a target list.
      The source list keeps its ticked lines. Duplicates on the target
      list are skipped (the per-list "unique stock item" invariant).

  POST /api/shopping-lists/<id>/lines/move-to/<target_id>
      Same move, but over an explicit set of `line_ids` — the bulk-select
      bar's "Move to list" action. One request for the whole selection,
      not one per line (the FU-713/714 shape).

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

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.shopping_list import (ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation, ok,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


# ───── Move lines → existing list ─────────────────────────────────────────

@dataclass(slots=True)
class MoveLinesResponse:
    source_not_found: bool = False
    target_not_found: bool = False
    same_list: bool = False
    target_archived: bool = False
    moved_count: int = 0
    skipped_duplicates: int = 0


class MoveLinesHandler:
    """Moves lines from one list onto another.

    Two callers, one body of rules: "move everything unticked" (the finish
    flow's offer to carry the leftovers forward) and "move exactly these"
    (the bulk-select bar). Both need the same duplicate skipping, the same
    archived-target guard and the same sequence appending, so `line_ids` is
    a filter on one handler rather than a second near-copy of it — the
    duplicate-skipping rule is the kind that drifts when it lives twice.
    """
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(
        self,
        source_id: UUID,
        target_id: UUID,
        line_ids: List[UUID] | None = None,
    ) -> MoveLinesResponse:
        """`line_ids=None` means "every unticked line on the source list";
        an explicit list moves exactly those, ticked or not."""
        if source_id == target_id:
            return MoveLinesResponse(same_list=True)

        source = self.repository.get(ShoppingList).by_id(source_id)
        if source is None:
            return MoveLinesResponse(source_not_found=True)
        target = self.repository.get(ShoppingList).by_id(target_id)
        if target is None:
            return MoveLinesResponse(target_not_found=True)
        if target.is_done:
            return MoveLinesResponse(target_archived=True)

        source_filter = EntityField(
            ShoppingListLine, "shopping_list_id"
        ).eq(source_id)
        if line_ids is None:
            source_filter = source_filter & EntityField(
                ShoppingListLine, ShoppingListLine.Fields.IS_TICKED
            ).eq(False)
        else:
            # Scoped to the source list on purpose: an id from another list
            # must not be movable by passing it here.
            source_filter = source_filter & EntityField(
                ShoppingListLine, "id"
            ).in_(list(line_ids))
        movable: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            source_filter
        )
        target_lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(target_id)
        )
        target_item_ids = {l.stock_item_id for l in target_lines}
        next_sequence = (max((l.sequence for l in target_lines), default=-1)) + 1

        moved = 0
        skipped = 0
        for line in movable:
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
        return MoveLinesResponse(moved_count=moved, skipped_duplicates=skipped)


@SHOPPING_LIST_ROUTER.route(
    "/<uuid:source_id>/move-unticked-to/<uuid:target_id>", methods=["POST"]
)
def move_unticked_to(source_id: UUID, target_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = MoveLinesHandler(SqlAlchemyRepository()).handle(source_id, target_id)
    _Error = _move_error_response(_Response, source_id, target_id)
    if _Error is not None:
        return _Error
    _Logger.info(
        f"Moved {_Response.moved_count} unticked line(s) from {source_id} -> {target_id} "
        f"({_Response.skipped_duplicates} duplicates skipped)"
    )
    return ok({
        "moved_count": _Response.moved_count,
        "skipped_duplicates": _Response.skipped_duplicates,
    })


class MoveLinesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line_ids: List[UUID] = Field(min_length=1)


@SHOPPING_LIST_ROUTER.route(
    "/<uuid:source_id>/lines/move-to/<uuid:target_id>", methods=["POST"]
)
@has_request_body(MoveLinesRequest)
def move_lines_to(source_id: UUID, target_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: MoveLinesRequest = get_request_body()
    _Response = MoveLinesHandler(SqlAlchemyRepository()).handle(
        source_id, target_id, _Request.line_ids
    )
    _Error = _move_error_response(_Response, source_id, target_id)
    if _Error is not None:
        return _Error
    _Logger.info(
        f"Moved {_Response.moved_count} selected line(s) from {source_id} -> {target_id} "
        f"({_Response.skipped_duplicates} duplicates skipped)"
    )
    return ok({
        "moved_count": _Response.moved_count,
        "skipped_duplicates": _Response.skipped_duplicates,
    })


def _move_error_response(
    response: MoveLinesResponse, source_id: UUID, target_id: UUID
):
    """None when the move succeeded; otherwise the error to return."""
    if response.source_not_found:
        return not_found("ShoppingList (source)", source_id)
    if response.target_not_found:
        return not_found("ShoppingList (target)", target_id)
    if response.same_list:
        return business_rule_violation("Source and target lists are the same.")
    if response.target_archived:
        return business_rule_violation(
            "Cannot move items to an archived list. Unarchive it first."
        )
    return None


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

    A future iteration could trigger a fresh push per product, but that
    crosses into ingestion-producer territory and is out of scope here.
    """

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

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


@SHOPPING_LIST_ROUTER.route("/<uuid:shopping_list_id>/refresh-deals", methods=["POST"])
def refresh_deals(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = RefreshDealsHandler(SqlAlchemyRepository()).handle(shopping_list_id)
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
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

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


@SHOPPING_LIST_ROUTER.route("/<uuid:shopping_list_id>/clear", methods=["POST"])
def clear_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = ClearListHandler(SqlAlchemyRepository()).handle(shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(f"Cleared {_Response.removed_count} lines from list {shopping_list_id}")
    return ok({"removed_count": _Response.removed_count})


# ───── Discard the unticked lines ─────────────────────────────────────────

@dataclass(slots=True)
class DiscardUntickedResponse:
    not_found: bool = False
    removed_count: int = 0


class DiscardUntickedHandler:
    """Deletes every unticked line on a list.

    The finish flow's third disposition, alongside move-to-existing and
    move-to-new. A finished list is a receipt, and a receipt doesn't record
    what you didn't buy — leaving the leftovers in place stranded them on an
    archived list forever and kept them counted in the dashboard's "queued"
    card. So the finish dialog now makes the user choose, and this is the
    "I didn't want them after all" branch.

    One request rather than a delete-per-line loop: the same reason the bulk
    endpoints exist.
    """
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, shopping_list_id: UUID) -> DiscardUntickedResponse:
        lst = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return DiscardUntickedResponse(not_found=True)
        lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
            & EntityField(ShoppingListLine, ShoppingListLine.Fields.IS_TICKED).eq(False)
        )
        for line in lines:
            self.repository.remove(line)
        self.repository.save_changes()
        return DiscardUntickedResponse(removed_count=len(lines))


@SHOPPING_LIST_ROUTER.route(
    "/<uuid:shopping_list_id>/discard-unticked", methods=["POST"]
)
def discard_unticked(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = DiscardUntickedHandler(SqlAlchemyRepository()).handle(shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(
        f"Discarded {_Response.removed_count} unticked line(s) from list {shopping_list_id}"
    )
    return ok({"removed_count": _Response.removed_count})
