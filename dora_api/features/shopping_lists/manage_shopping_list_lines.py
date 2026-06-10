"""Add / update / delete shopping list lines, plus quick-add to primary.

Lines are the per-stock-item rows on a list. Endpoints:

  POST   /api/shopping-lists/<id>/lines        — add a line
  PATCH  /api/shopping-lists/<id>/lines/<lid>  — tick, quantity, selected_product
  DELETE /api/shopping-lists/<id>/lines/<lid>
  POST   /api/shopping-lists/primary/lines     — quick-add (DRAFT-count inference)

P6-01 Chunk 2: "primary" is no longer a stored flag — quick-add resolves the
target by counting DRAFT lists (see primary_target_resolver.py). The client may
pass `shopping_list_id` to disambiguate the 2+ case (and remember the pick in
sessionStorage).
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.shopping_list import (ADDED_VIA_MANUAL,
                                                    SHOPPING_LIST_STATUS_DONE,
                                                    SHOPPING_LIST_STATUS_DRAFT,
                                                    ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.features.shopping_lists.primary_target_resolver import (
    PrimaryTargetCandidate, resolve_primary_target)
from dora_api.infrastructure.api_response import (business_rule_violation, ok,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# ───── Add line ───────────────────────────────────────────────────────────

class AddLineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # C-7 Chunk 3 — a line may anchor on a stock item, a product, or
    # both. At least one MUST be set; validated below + at the DB
    # (CHECK ck_shopping_list_line_anchor). `product_id` enables the
    # "standalone product line" path (L130 / L191 rule 1): a product
    # whose linked stock item isn't on the list adds as its own row.
    stock_item_id: UUID | None = None
    product_id: UUID | None = None
    quantity: int | None = Field(default=1, ge=0)
    selected_product_id: UUID | None = None


@dataclass(slots=True)
class AddLineResponse:
    line_id: UUID | None = None
    list_not_found: bool = False
    item_not_found: bool = False
    product_not_found: bool = False
    no_anchor: bool = False
    already_on_list: bool = False


class AddLineHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: AddLineRequest, shopping_list_id: UUID) -> AddLineResponse:
        # C-7 Chunk 3 — anchor validation. At least one of
        # stock_item_id/product_id is required; the DB enforces it too
        # but failing early gives the SPA a clean 400.
        if request.stock_item_id is None and request.product_id is None:
            return AddLineResponse(no_anchor=True)

        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return AddLineResponse(list_not_found=True)

        if request.stock_item_id is not None:
            item: StockItem | None = self.repository.get(StockItem).by_id(request.stock_item_id)
            if item is None:
                return AddLineResponse(item_not_found=True)
        if request.product_id is not None:
            product: Product | None = self.repository.get(Product).by_id(request.product_id)
            if product is None:
                return AddLineResponse(product_not_found=True)

        # C-7 Chunk 3 — dedupe by anchor. Same stock_item_id OR same
        # product_id on the same list = already on list. (A product
        # nested under a stock item carries both columns; either
        # match counts.)
        sibling_lines = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
        )
        existing = None
        for sibling in sibling_lines:
            if (
                request.stock_item_id is not None
                and sibling.stock_item_id == request.stock_item_id
                and sibling.product_id is None
            ):
                existing = sibling
                break
            if (
                request.product_id is not None
                and sibling.product_id == request.product_id
            ):
                existing = sibling
                break
        if existing is not None:
            return AddLineResponse(line_id=existing.id, already_on_list=True)

        # Sequence = current max + 1 so new lines append.
        next_sequence = (max((l.sequence for l in sibling_lines), default=-1)) + 1

        line = ShoppingListLine(
            shopping_list_id = shopping_list_id,
            stock_item_id = request.stock_item_id,
            product_id = request.product_id,
            quantity = request.quantity,
            selected_product_id = request.selected_product_id,
            sequence = next_sequence,
            added_via = ADDED_VIA_MANUAL,
            added_at = datetime.now(timezone.utc),
        )
        self.repository.add(line)
        # State-ownership Chunk 6 — snapshot the offer at *add* (not at
        # tick) so "what did I mean to pay?" stays answerable for lines
        # that never get ticked, and so a price move between add and
        # tick doesn't silently overwrite the planning-time intent.
        if line.selected_product_id is not None:
            snapshot_offer_price(self.repository, line)
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
    if _Response.no_anchor:
        return business_rule_violation(
            "A line needs at least one of stock_item_id or product_id."
        )
    if _Response.item_not_found and _Request.stock_item_id is not None:
        return not_found("StockItem", _Request.stock_item_id)
    if _Response.product_not_found and _Request.product_id is not None:
        return not_found("Product", _Request.product_id)
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
        # Path params arrive as str; the entity's FK is a UUID. Compare as
        # strings so the parent-ownership guard doesn't always mismatch.
        if line is None or str(line.shopping_list_id) != str(shopping_list_id):
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
            # State-ownership Chunk 6 — ticking is "purchase complete",
            # NOT "commit to an offer". The snapshot was captured at
            # add-time / selection-change time and represents the
            # planning-moment price; ticking leaves it alone. Untick
            # likewise preserves it (the commit-to-offer moment didn't
            # un-happen).
            #
            # Belt-and-braces for legacy rows that landed before the
            # add-time snapshot existed and never got one assigned: on
            # the first tick, fill it from the current offer so reports
            # have something to read. New rows reach this path with
            # `picked_offer_price` already set from add/select.
            became_ticked = request.is_ticked and not line.is_ticked
            line.is_ticked = request.is_ticked
            if became_ticked and line.picked_offer_price is None:
                snapshot_offer_price(self.repository, line)
        if "sequence" in set_fields and request.sequence is not None:
            line.sequence = request.sequence
        if request.clear_selected_product:
            line.selected_product_id = None
            # Snapshot belongs to the (now-cleared) selection; clear it
            # so totals fall back to "no priced intent" instead of
            # showing a stale price for an offer the user no longer
            # picked.
            line.picked_offer_price = None
            line.list_price_at_pick = None
            user_edited = True
        elif "selected_product_id" in set_fields and request.selected_product_id is not None:
            changed = line.selected_product_id != request.selected_product_id
            line.selected_product_id = request.selected_product_id
            # State-ownership Chunk 6 — re-snapshot whenever the user
            # commits to a different offer. The price they "meant to
            # pay" just changed.
            if changed:
                snapshot_offer_price(self.repository, line)
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
        # Path params arrive as str; the entity's FK is a UUID. Compare as
        # strings so the parent-ownership guard doesn't always mismatch.
        if line is None or str(line.shopping_list_id) != str(shopping_list_id):
            return DeleteLineResponse(line_not_found=True)
        # C-7 Chunk 3, rule 3 — when a stock-item-anchored line is
        # removed, cascade-remove any nested product-only lines on
        # the same list whose product is linked to that stock item.
        # A "nested product line" here = product_id set, stock_item_id
        # null, on the same list, where the product appears under the
        # removed item's `products` relationship.
        if line.stock_item_id is not None and line.product_id is None:
            stock_item = (
                self.repository.get(StockItem)
                .include(StockItem.Fields.PRODUCTS)
                .by_id(line.stock_item_id)
            )
            if stock_item is not None:
                product_ids = {p.id for p in (stock_item.products or [])}
                if product_ids:
                    nested = self.repository.get(ShoppingListLine).all(
                        EntityField(ShoppingListLine, "shopping_list_id").eq(line.shopping_list_id)
                        & EntityField(ShoppingListLine, "stock_item_id").is_null()
                        & EntityField(ShoppingListLine, "product_id").in_(list(product_ids))
                    )
                    for child in nested:
                        self.repository.remove(child)
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
            # C-7 Chunk 3, rule 3 — cascade-remove nested product
            # lines (same rule as the by-line delete; see comment
            # above DeleteLineHandler).
            stock_item = (
                self.repository.get(StockItem)
                .include(StockItem.Fields.PRODUCTS)
                .by_id(stock_item_id)
            )
            if stock_item is not None:
                product_ids = {p.id for p in (stock_item.products or [])}
                if product_ids:
                    nested = self.repository.get(ShoppingListLine).all(
                        EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
                        & EntityField(ShoppingListLine, "stock_item_id").is_null()
                        & EntityField(ShoppingListLine, "product_id").in_(list(product_ids))
                    )
                    for child in nested:
                        self.repository.remove(child)
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


# ───── Quick-add to inferred primary ──────────────────────────────────────

class QuickAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_item_id: UUID
    # If the client has resolved the ambiguous (2+ drafts) case — e.g. via the
    # sessionStorage pick — it sends the chosen list here. The server still
    # validates that it's a draft.
    shopping_list_id: UUID | None = None


@dataclass(slots=True)
class QuickAddResponse:
    # Discriminator on `result`: "added" | "no_draft" | "ambiguous" |
    # "item_not_found" | "hint_invalid".
    result: str = "added"
    line_id: UUID | None = None
    shopping_list_id: UUID | None = None
    already_on_list: bool = False
    candidates: list[PrimaryTargetCandidate] | None = None


class QuickAddToPrimaryHandler:
    """Resolves the quick-add target by DRAFT-count inference (Chunk 2) and
    adds a line. The client may pass `shopping_list_id` to resolve the
    ambiguous (2+ drafts) case; sessionStorage on the client remembers the
    pick for the rest of the tab session.
    """

    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: QuickAddRequest) -> QuickAddResponse:
        item: StockItem | None = self.repository.get(StockItem).by_id(request.stock_item_id)
        if item is None:
            return QuickAddResponse(result="item_not_found")

        target: ShoppingList | None
        if request.shopping_list_id is not None:
            target = self.repository.get(ShoppingList).by_id(request.shopping_list_id)
            if target is None or target.status != SHOPPING_LIST_STATUS_DRAFT:
                return QuickAddResponse(result="hint_invalid")
        else:
            active_lists = self.repository.get(ShoppingList).all(
                EntityField(ShoppingList, ShoppingList.Fields.STATUS).ne(SHOPPING_LIST_STATUS_DONE)
            )
            outcome = resolve_primary_target(active_lists)
            if outcome.kind == "none":
                return QuickAddResponse(result="no_draft")
            if outcome.kind == "ambiguous":
                return QuickAddResponse(result="ambiguous", candidates=outcome.candidates)
            target = next(
                (l for l in active_lists if l.id == outcome.target_list_id), None
            )
            if target is None:  # defensive; resolver guarantees this id is in `lists`
                return QuickAddResponse(result="no_draft")

        existing = self.repository.get(ShoppingListLine).one(
            EntityField(ShoppingListLine, "shopping_list_id").eq(target.id)
            & EntityField(ShoppingListLine, "stock_item_id").eq(request.stock_item_id)
        )
        if existing is not None:
            return QuickAddResponse(
                result="added",
                line_id=existing.id,
                shopping_list_id=target.id,
                already_on_list=True,
            )

        siblings = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(target.id)
        )
        next_sequence = (max((l.sequence for l in siblings), default=-1)) + 1
        line = ShoppingListLine(
            shopping_list_id = target.id,
            stock_item_id = request.stock_item_id,
            quantity = 1,
            sequence = next_sequence,
            added_via = ADDED_VIA_MANUAL,
            added_at = datetime.now(timezone.utc),
        )
        self.repository.add(line)
        self.repository.save_changes()
        return QuickAddResponse(
            result="added", line_id=line.id, shopping_list_id=target.id
        )


@SHOPPING_LIST_ROUTER.route("/primary/lines", methods=["POST"])
@has_request_body(QuickAddRequest)
def quick_add_to_primary():
    _Logger = logging.getLogger(__name__)
    _Request: QuickAddRequest = get_request_body()
    _Response = get_container().inject(QuickAddToPrimaryHandler).handle(_Request)
    if _Response.result == "item_not_found":
        return not_found("StockItem", _Request.stock_item_id)
    if _Response.result == "hint_invalid":
        return business_rule_violation(
            "The chosen shopping list is not a draft."
        )
    if _Response.result == "no_draft":
        # Not a 404 — there may be SHOPPING/DONE lists, just no draft. The
        # client surfaces a "create a list?" prompt.
        return ok({"result": "no_draft"})
    if _Response.result == "ambiguous":
        return ok({
            "result": "ambiguous",
            "candidates": [
                {"shopping_list_id": c.shopping_list_id, "name": c.name}
                for c in (_Response.candidates or [])
            ],
        })
    _Logger.info(
        f"Quick-added stock item {_Request.stock_item_id} to list "
        f"{_Response.shopping_list_id} (already_on_list={_Response.already_on_list})"
    )
    return ok({
        "result": "added",
        "shopping_list_id": _Response.shopping_list_id,
        "line_id": _Response.line_id,
        "already_on_list": _Response.already_on_list,
    })
