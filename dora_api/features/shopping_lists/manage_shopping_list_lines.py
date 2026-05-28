"""Add / update / delete shopping list lines, plus quick-add to primary.

Lines are the per-stock-item rows on a list. Endpoints:

  POST   /api/shopping-lists/<id>/lines        — add a line
  PATCH  /api/shopping-lists/<id>/lines/<lid>  — tick, quantity, selected_product
  DELETE /api/shopping-lists/<id>/lines/<lid>
  POST   /api/shopping-lists/primary/lines     — quick-add to primary list

The primary-list shortcut exists so the stock-overview cart button doesn't
need to know which list is primary; the server resolves it.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.shopping_list import (ADDED_VIA_MANUAL,
                                                    ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation, ok,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# ───── Add line ───────────────────────────────────────────────────────────

class AddLineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_item_id: UUID
    quantity: int | None = Field(default=1, ge=0)
    selected_product_id: UUID | None = None


@dataclass(slots=True)
class AddLineResponse:
    line_id: UUID | None = None
    list_not_found: bool = False
    item_not_found: bool = False
    already_on_list: bool = False


class AddLineHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: AddLineRequest, shopping_list_id: UUID) -> AddLineResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return AddLineResponse(list_not_found=True)

        item: StockItem | None = self.repository.get(StockItem).by_id(request.stock_item_id)
        if item is None:
            return AddLineResponse(item_not_found=True)

        # Prevent adding the same stock item to a list twice — the spec
        # treats lines as unique-per-item and folds quantity into the same
        # row instead.
        existing = self.repository.get(ShoppingListLine).one(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
            & EntityField(ShoppingListLine, "stock_item_id").eq(request.stock_item_id)
        )
        if existing is not None:
            return AddLineResponse(line_id=existing.id, already_on_list=True)

        # Sequence = current max + 1 so new lines append.
        siblings = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
        )
        next_sequence = (max((l.sequence for l in siblings), default=-1)) + 1

        line = ShoppingListLine(
            shopping_list_id = shopping_list_id,
            stock_item_id = request.stock_item_id,
            quantity = request.quantity,
            selected_product_id = request.selected_product_id,
            sequence = next_sequence,
            added_via = ADDED_VIA_MANUAL,
            added_at = datetime.now(timezone.utc),
        )
        self.repository.add(line)
        self.repository.save_changes()
        return AddLineResponse(line_id=line.id)


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/lines", methods=["POST"])
@has_request_body(AddLineRequest)
def add_line(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: AddLineRequest = get_request_body()
    _Response = get_container().inject(AddLineHandler).handle(_Request, shopping_list_id)
    if _Response.list_not_found:
        return not_found("ShoppingList", shopping_list_id)
    if _Response.item_not_found:
        return not_found("StockItem", _Request.stock_item_id)
    _Logger.info(
        f"Added line {_Response.line_id} to shopping list {shopping_list_id} "
        f"(stock_item={_Request.stock_item_id}, already_on_list={_Response.already_on_list})"
    )
    return ok({
        "line_id": _Response.line_id,
        "already_on_list": _Response.already_on_list,
    })


# ───── Price snapshot helper (N6) ─────────────────────────────────────────

def snapshot_offer_price(repository: SqlAlchemyRepository, line: ShoppingListLine) -> None:
    """Freeze the current offer of `line.selected_product_id` onto the line.
    No-op when the line has no selection, or no current offer exists for
    that product. Designed to be called once, when the line first ticks.
    """
    if line.selected_product_id is None:
        return
    offer: ProductOffer | None = repository.get(ProductOffer).one(
        EntityField(ProductOffer, "_product_id").eq(line.selected_product_id)
    )
    if offer is None:
        return
    line.picked_offer_price = float(offer.price_now)
    line.list_price_at_pick = float(offer.price_was) if offer.price_was else None


# Internal alias used by the update path; exposed name above is what other
# modules (e.g. finish-list) import.
_snapshot_offer_price = snapshot_offer_price


# ───── Update line (tick, quantity, selected_product) ─────────────────────

class UpdateLineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quantity: int | None = Field(default=None, ge=0)
    is_ticked: bool | None = None
    selected_product_id: UUID | None = None
    # `None` for selected_product_id is ambiguous (clear vs unset). Use this
    # explicit flag to clear an existing selection.
    clear_selected_product: bool = False
    sequence: int | None = None
    # P2-02 purchase memory overrides. Same clear-vs-unset story as the
    # selected_product fields: clients send the explicit clear_* flag to
    # blank a previously-recorded actual price/merchant, otherwise omitted
    # fields are left untouched.
    actual_unit_price: float | None = Field(default=None, ge=0)
    clear_actual_unit_price: bool = False
    purchased_merchant_id: UUID | None = None
    clear_purchased_merchant: bool = False


@dataclass(slots=True)
class UpdateLineResponse:
    line_not_found: bool = False


class UpdateLineHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(
        self,
        request: UpdateLineRequest,
        shopping_list_id: UUID,
        line_id: UUID,
    ) -> UpdateLineResponse:
        line: ShoppingListLine | None = self.repository.get(ShoppingListLine).by_id(line_id)
        if line is None or line.shopping_list_id != shopping_list_id:
            return UpdateLineResponse(line_not_found=True)

        set_fields = request.model_fields_set
        # Track whether the user is editing substantive fields — qty or
        # selected_product. If so, an auto_ provenance flips back to
        # "manual" (the user has taken ownership of the line). Ticking
        # alone doesn't count: it's a shopping-mode action, not editing.
        user_edited = False
        if "quantity" in set_fields:
            line.quantity = request.quantity
            user_edited = True
        if "is_ticked" in set_fields and request.is_ticked is not None:
            # N6: snapshot the selected offer's price the first time a line
            # transitions to ticked. Re-ticking after an untick doesn't
            # re-snapshot — the original moment-of-pick wins so reports
            # stay stable. Untick clears the snapshot so a future tick can
            # capture a fresh one.
            became_ticked = request.is_ticked and not line.is_ticked
            line.is_ticked = request.is_ticked
            if became_ticked and line.picked_offer_price is None:
                _snapshot_offer_price(self.repository, line)
            elif not request.is_ticked:
                line.picked_offer_price = None
                line.list_price_at_pick = None
        if "sequence" in set_fields and request.sequence is not None:
            line.sequence = request.sequence
        if request.clear_selected_product:
            line.selected_product_id = None
            user_edited = True
        elif "selected_product_id" in set_fields and request.selected_product_id is not None:
            line.selected_product_id = request.selected_product_id
            user_edited = True

        # P2-02 — actual paid price / merchant. Editing these doesn't flip
        # added_via back to manual: they're a shopping-mode capture, not a
        # re-curation of how the line came to be on the list.
        if request.clear_actual_unit_price:
            line.actual_unit_price = None
        elif "actual_unit_price" in set_fields and request.actual_unit_price is not None:
            line.actual_unit_price = float(request.actual_unit_price)
        if request.clear_purchased_merchant:
            line.purchased_merchant_id = None
        elif "purchased_merchant_id" in set_fields and request.purchased_merchant_id is not None:
            line.purchased_merchant_id = request.purchased_merchant_id

        if user_edited and line.added_via != ADDED_VIA_MANUAL:
            line.added_via = ADDED_VIA_MANUAL

        self.repository.save_changes()
        return UpdateLineResponse()


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/lines/<line_id>", methods=["PATCH"])
@has_request_body(UpdateLineRequest)
def update_line(shopping_list_id: UUID, line_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: UpdateLineRequest = get_request_body()
    _Response = get_container().inject(UpdateLineHandler).handle(_Request, shopping_list_id, line_id)
    if _Response.line_not_found:
        return not_found("ShoppingListLine", line_id)
    _Logger.debug(f"Updated line {line_id} on list {shopping_list_id}")
    return no_content()


# ───── Delete line ────────────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteLineResponse:
    line_not_found: bool = False


class DeleteLineHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, shopping_list_id: UUID, line_id: UUID) -> DeleteLineResponse:
        line: ShoppingListLine | None = self.repository.get(ShoppingListLine).by_id(line_id)
        if line is None or line.shopping_list_id != shopping_list_id:
            return DeleteLineResponse(line_not_found=True)
        self.repository.remove(line)
        self.repository.save_changes()
        return DeleteLineResponse()


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/lines/<line_id>", methods=["DELETE"])
def delete_line(shopping_list_id: UUID, line_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(DeleteLineHandler).handle(shopping_list_id, line_id)
    if _Response.line_not_found:
        return not_found("ShoppingListLine", line_id)
    _Logger.info(f"Deleted line {line_id} from list {shopping_list_id}")
    return no_content()


# ───── Remove by stock-item (cart-button quick-remove path) ──────────────

@dataclass(slots=True)
class RemoveByStockItemResponse:
    list_not_found: bool = False
    removed: bool = False


class RemoveLineByStockItemHandler:
    """Used by the stock overview's cart button when the user clicks on an
    already-listed item — we don't carry the line_id around, just the
    stock_item_id. Idempotent: removing an item that isn't on the list
    is a no-op (still 204) so the client doesn't have to special-case the
    race where another tab already removed it.
    """

    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, shopping_list_id: UUID, stock_item_id: UUID) -> RemoveByStockItemResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return RemoveByStockItemResponse(list_not_found=True)

        existing = self.repository.get(ShoppingListLine).one(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
            & EntityField(ShoppingListLine, "stock_item_id").eq(stock_item_id)
        )
        if existing is not None:
            self.repository.remove(existing)
            self.repository.save_changes()
            return RemoveByStockItemResponse(removed=True)
        return RemoveByStockItemResponse()


@SHOPPING_LIST_ROUTER.route(
    "/<shopping_list_id>/lines/by-stock-item/<stock_item_id>", methods=["DELETE"]
)
def remove_line_by_stock_item(shopping_list_id: UUID, stock_item_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(RemoveLineByStockItemHandler).handle(
        shopping_list_id, stock_item_id,
    )
    if _Response.list_not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(
        f"Cart-remove on list {shopping_list_id} for item {stock_item_id}: "
        f"removed={_Response.removed}"
    )
    return no_content()


# ───── Quick-add to primary ───────────────────────────────────────────────

class QuickAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_item_id: UUID


@dataclass(slots=True)
class QuickAddResponse:
    line_id: UUID | None = None
    shopping_list_id: UUID | None = None
    no_primary: bool = False
    item_not_found: bool = False
    already_on_list: bool = False


class QuickAddToPrimaryHandler:
    """Resolves the current primary shopping list and adds a line. Used by
    the stock-overview cart button — one round-trip from click to a
    line-on-list, no upfront "which list?" prompt needed.
    """

    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: QuickAddRequest) -> QuickAddResponse:
        primary: ShoppingList | None = self.repository.get(ShoppingList).one(
            EntityField(ShoppingList, ShoppingList.Fields.IS_PRIMARY).eq(True)
            & EntityField(ShoppingList, ShoppingList.Fields.IS_ARCHIVED).eq(False)
        )
        if primary is None:
            return QuickAddResponse(no_primary=True)
        item: StockItem | None = self.repository.get(StockItem).by_id(request.stock_item_id)
        if item is None:
            return QuickAddResponse(item_not_found=True)

        existing = self.repository.get(ShoppingListLine).one(
            EntityField(ShoppingListLine, "shopping_list_id").eq(primary.id)
            & EntityField(ShoppingListLine, "stock_item_id").eq(request.stock_item_id)
        )
        if existing is not None:
            return QuickAddResponse(
                line_id=existing.id,
                shopping_list_id=primary.id,
                already_on_list=True,
            )

        siblings = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(primary.id)
        )
        next_sequence = (max((l.sequence for l in siblings), default=-1)) + 1
        line = ShoppingListLine(
            shopping_list_id = primary.id,
            stock_item_id = request.stock_item_id,
            quantity = 1,
            sequence = next_sequence,
            added_via = ADDED_VIA_MANUAL,
            added_at = datetime.now(timezone.utc),
        )
        self.repository.add(line)
        self.repository.save_changes()
        return QuickAddResponse(line_id=line.id, shopping_list_id=primary.id)


@SHOPPING_LIST_ROUTER.route("/primary/lines", methods=["POST"])
@has_request_body(QuickAddRequest)
def quick_add_to_primary():
    _Logger = logging.getLogger(__name__)
    _Request: QuickAddRequest = get_request_body()
    _Response = get_container().inject(QuickAddToPrimaryHandler).handle(_Request)
    if _Response.no_primary:
        # Specifically NOT a 404 — there are lists, just none flagged
        # primary. The frontend uses this signal to prompt the user to
        # pick one.
        return business_rule_violation("No primary shopping list is set.")
    if _Response.item_not_found:
        return not_found("StockItem", _Request.stock_item_id)
    _Logger.info(
        f"Quick-added stock item {_Request.stock_item_id} to primary list "
        f"{_Response.shopping_list_id} (already_on_list={_Response.already_on_list})"
    )
    return ok({
        "shopping_list_id": _Response.shopping_list_id,
        "line_id": _Response.line_id,
        "already_on_list": _Response.already_on_list,
    })
