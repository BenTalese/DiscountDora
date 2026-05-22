"""Bigger-than-CRUD actions on shopping lists.

Bundled together because they share assumptions ("act on a list", "skip
ticked items where it matters", "pick a default merchant offer"). Splitting
each into its own file would just spread the same imports five ways.

Endpoints:

  POST /api/shopping-lists/autogenerate
      Build a new list (or top up an existing one) from stock items that
      are flagged AND low-or-out.

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
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from dora_api.domain.entities.shopping_list import (ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation, ok,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Stock levels that the auto-generator treats as "needs restocking".
# Matches the attention-engine constants but kept local so changes here
# don't accidentally retune the heatmap.
LOW_OR_OUT_SEQUENCES = (2, 3)


# ───── Auto-generate ──────────────────────────────────────────────────────

class AutogenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # If set, lines are appended to this list. If null, a fresh list is
    # created (and made primary when there's no current primary).
    target_shopping_list_id: UUID | None = None
    # Optional override for the new list's name. Ignored when targeting an
    # existing list.
    name: str | None = None
    # If True, *all* flagged items go onto the list, not just the low/out
    # ones. Useful for "shop the staples" lists. Only honoured when
    # source='flagged'.
    include_well_stocked: bool = False
    # Which catalogue of items to pull from.
    #   flagged    — essentials marked is_flagged (current behaviour).
    #   low_or_out — every item whose level is Low or Out, flagged or not.
    # The latter is for "fill the trolley with whatever's run down" runs;
    # the former for "shop the staples I care about most".
    source: Literal["flagged", "low_or_out"] = "flagged"


@dataclass(slots=True)
class AutogenerateResponse:
    target_shopping_list_id: UUID | None = None
    target_not_found: bool = False
    nothing_flagged: bool = False
    added_count: int = 0
    skipped_already_on_list: int = 0


class AutogenerateHandler:
    """Builds (or tops up) a shopping list from flagged-and-low items.

    Resolution order:
      1. Find every StockItem with `is_flagged=True`.
      2. (Default) Keep only those whose stock_level.sequence is in
         LOW_OR_OUT_SEQUENCES.
      3. Append to the target list (existing or freshly-created), skipping
         items already on that list so the call is idempotent.
    """

    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: AutogenerateRequest) -> AutogenerateResponse:
        # ── Pick / create the target list ─────────────────────────────────
        target: ShoppingList | None = None
        if request.target_shopping_list_id is not None:
            target = self.repository.get(ShoppingList).by_id(
                request.target_shopping_list_id
            )
            if target is None or target.is_archived:
                return AutogenerateResponse(target_not_found=True)
        else:
            now = datetime.now(timezone.utc)
            target = ShoppingList(
                name=(request.name or "").strip() or f"Auto · {now.strftime('%a %d %b')}",
                created_at=now,
            )
            # If there's no current primary list, the auto-generated one
            # becomes primary so cart buttons work immediately.
            current_primary = self.repository.get(ShoppingList).one(
                EntityField(ShoppingList, ShoppingList.Fields.IS_PRIMARY).eq(True)
                & EntityField(ShoppingList, ShoppingList.Fields.IS_ARCHIVED).eq(False)
            )
            if current_primary is None:
                target.is_primary = True
            self.repository.add(target)
            self.repository.save_changes()

        # ── Select source items ──────────────────────────────────────────
        # 'flagged'  → essentials, optionally filtered to low/out.
        # 'low_or_out' → every item that's low or out, regardless of flag.
        if request.source == "low_or_out":
            candidate_items: List[StockItem] = (
                self.repository.get(StockItem)
                .include(StockItem.Fields.STOCK_LEVEL)
                .all()
            )
            candidate_items = [
                i for i in candidate_items
                if i.stock_level is not None
                and getattr(i.stock_level, "sequence", -1) in LOW_OR_OUT_SEQUENCES
            ]
        else:
            candidate_items = (
                self.repository.get(StockItem)
                .include(StockItem.Fields.STOCK_LEVEL)
                .all(EntityField(StockItem, StockItem.Fields.IS_FLAGGED).eq(True))
            )
            if not request.include_well_stocked:
                candidate_items = [
                    i for i in candidate_items
                    if i.stock_level is not None
                    and getattr(i.stock_level, "sequence", -1) in LOW_OR_OUT_SEQUENCES
                ]

        if not candidate_items:
            return AutogenerateResponse(
                target_shopping_list_id=target.id, nothing_flagged=True
            )

        # ── Find existing line stock_item_ids so we don't double-add ─────
        existing_lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(target.id)
        )
        existing_item_ids = {l.stock_item_id for l in existing_lines}
        next_sequence = (max((l.sequence for l in existing_lines), default=-1)) + 1

        added = 0
        skipped = 0
        for item in candidate_items:
            if item.id in existing_item_ids:
                skipped += 1
                continue
            self.repository.add(ShoppingListLine(
                shopping_list_id=target.id,
                stock_item_id=item.id,
                quantity=1,
                sequence=next_sequence,
            ))
            next_sequence += 1
            added += 1

        self.repository.save_changes()
        return AutogenerateResponse(
            target_shopping_list_id=target.id,
            added_count=added,
            skipped_already_on_list=skipped,
        )


@SHOPPING_LIST_ROUTER.route("/autogenerate", methods=["POST"])
@has_request_body(AutogenerateRequest)
def autogenerate():
    _Logger = logging.getLogger(__name__)
    _Request: AutogenerateRequest = get_request_body()
    _Response = get_container().inject(AutogenerateHandler).handle(_Request)
    if _Response.target_not_found:
        return not_found("ShoppingList", _Request.target_shopping_list_id or "?")
    _Logger.info(
        f"Auto-generated onto list {_Response.target_shopping_list_id}: "
        f"+{_Response.added_count} added, {_Response.skipped_already_on_list} already on list"
    )
    return ok({
        "shopping_list_id": _Response.target_shopping_list_id,
        "added_count": _Response.added_count,
        "skipped_already_on_list": _Response.skipped_already_on_list,
        "nothing_flagged": _Response.nothing_flagged,
    })


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
        if target.is_archived:
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
