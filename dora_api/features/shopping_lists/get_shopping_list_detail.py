"""GET /api/shopping-lists/<id> — full detail with lines + linked products.

Each line carries enough info to render the row without further fetches:
stock item name + level, selected offer (if chosen) and *all* offers (so the
user can pick), and current ticked/quantity state. Totals are computed
client-side from the offers so we don't have to round-trip on tick.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List
from uuid import UUID

from dora_api.domain.entities.store import Store
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.shopping_list import (ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.preferred_buy import PreferredBuy
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.features.shopping_lists._line_price import line_paid_unit_price
from dora_api.features.stock_items.inference_overlay import (
    SURFACE_SHOPPING, resolve_divergence,
)
from dora_api.features.shopping_lists.shopping_list_attachment_access import (
    get_attachment_metadata_for_list)
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


@dataclass(frozen=True, slots=True)
class LineProductOfferDto:
    product_id: UUID
    name: str
    brand: str | None
    store_id: UUID
    store_name: str
    size: str | None
    price_now: float | None
    price_was: float | None
    is_selected: bool


# a stock item's PreferredBuy label as a pickable shopping hint.
@dataclass(frozen=True, slots=True)
class LinePreferredBuyDto:
    preferred_buy_id: UUID
    label: str


@dataclass(frozen=True, slots=True)
class ShoppingListLineDto:
    line_id: UUID
    # a line is anchored by stock_item_id OR product_id
    # (or both, when a product is nested under a stock item). NULL
    # stock_item_id ⇒ standalone-product line ("product only").
    stock_item_id: UUID | None
    product_id: UUID | None
    stock_item_name: str
    stock_level_name: str | None
    stock_location_id: UUID | None
    stock_location_breadcrumb: List[str]
    quantity: int | None
    is_ticked: bool
    selected_product_id: UUID | None
    sequence: int
    # X5 — line provenance ("manual" by default; one of the auto_* values
    # when X5 auto-generate or the auto-add-on-low trigger placed it here).
    # Drives the "auto: low stock" / "auto: recipe Tomato Soup" chip in
    # ShoppingListDetail.
    added_via: str
    added_at: datetime | None
    # what the shopper actually paid / where they
    # actually bought it. Both NULL until the user overrides on the line.
    actual_unit_price: float | None
    purchased_store_id: UUID | None
    purchased_store_name: str | None
    # server-resolved per-item price suggestion for the
    # till-entry editor, with a human source label. `None` when there's no
    # prior purchase and no offer to suggest. Display-only; the SPA seeds the
    # editor from it and persists on first edit (R-003 — the label is resolved
    # here, the client just renders the string).
    prefill_unit_price: float | None = None
    prefill_source_label: str | None = None
    offers: List[LineProductOfferDto] = field(default_factory=list)
    # the chosen hint + the item's available labels for the picker.
    preferred_buy_id: UUID | None = None
    preferred_buys: List[LinePreferredBuyDto] = field(default_factory=list)
    # trim-to-budget optimiser. True when this line has been set
    # aside by the "Trim to fit" pass; the SPA routes it into the
    # collapsible "Deferred to fit budget" section on the list-detail page
    # instead of the active list. Totals below skip deferred lines.
    # `deferred_reason` carries the chip vocab string from brief §5,
    # frozen at trim time.
    deferred_by_budget: bool = False
    deferred_reason: str | None = None
    # RD-18 (FU-407) — whether the anchoring stock item has any recorded
    # substitutes. Lets the SPA disable the "Swap with substitute" affordance
    # up front instead of surfacing it as a dead-end that toasts "no
    # substitutes recorded" only after a tap. False for product-only lines.
    has_substitutes: bool = False


@dataclass(frozen=True, slots=True)
class ShoppingListTotalsDto:
    """Server-owned list-level money/count aggregates (state-ownership Type B).

    The browser used to sum these across the fetched lines (the dashboard's
    `primaryListStats`); the server now owns the cross-line totals so the number
    can't silently disagree. Per-line *display* price stays a client concern
    (the accepted Type-C `priceOfLine` helper) — only the aggregate moved.
    """
    total_price: float        # full price of every line
    remaining_price: float    # price of un-ticked lines only ("still to grab")
    total_savings: float      # savings vs RRP across all lines
    unticked_count: int
    ticked_count: int
    line_count: int


def _chosen_offer(line: 'ShoppingListLineDto') -> 'LineProductOfferDto | None':
    """The offer a line's price is based on: the explicitly-selected one, else
    the first (the list is pre-sorted preferred→cheapest). Mirrors the client's
    `chosenOfferFor` exactly — both operate on the same server-sorted offers."""
    for offer in line.offers:
        if offer.is_selected:
            return offer
    return line.offers[0] if line.offers else None


def _line_price(line: 'ShoppingListLineDto') -> float:
    """Port of `priceOfLine` (shoppingList.ts): a user-entered actual price wins,
    else the chosen offer's `price_now`, times quantity."""
    qty = line.quantity or 1
    if line.actual_unit_price is not None:
        return line.actual_unit_price * qty
    offer = _chosen_offer(line)
    if offer is None or offer.price_now is None:
        return 0.0
    return offer.price_now * qty


def _line_savings(line: 'ShoppingListLineDto') -> float:
    """Port of `savingsOfLine`: (chosen offer RRP − paid) × qty, floored at 0."""
    offer = _chosen_offer(line)
    if offer is None or offer.price_was is None:
        return 0.0
    paid = line.actual_unit_price if line.actual_unit_price is not None else offer.price_now
    if paid is None:
        return 0.0
    diff = offer.price_was - paid
    if diff <= 0:
        return 0.0
    return diff * (line.quantity or 1)


def compute_list_totals(lines: List['ShoppingListLineDto']) -> ShoppingListTotalsDto:
    """Aggregate the per-line price/savings into list-level totals. Single source
    for the dashboard's primary-list stats (it reads these instead of summing).

    FU-448 — lines with `deferred_by_budget=True` are not part of the active
    list; they render under the Deferred section and don't count toward
    projected total, savings, or ticked/unticked counts."""
    total_price = 0.0
    remaining_price = 0.0
    total_savings = 0.0
    unticked = 0
    active_line_count = 0
    for line in lines:
        if line.deferred_by_budget:
            continue
        active_line_count += 1
        price = _line_price(line)
        total_price += price
        total_savings += _line_savings(line)
        if not line.is_ticked:
            remaining_price += price
            unticked += 1
    return ShoppingListTotalsDto(
        total_price = total_price,
        remaining_price = remaining_price,
        total_savings = total_savings,
        unticked_count = unticked,
        ticked_count = active_line_count - unticked,
        line_count = active_line_count,
    )


# receipt-photo attachment metadata. Bytes never inlined; the SPA
# loads each via `GET /shopping-lists/<list_id>/attachments/<id>`.
@dataclass(frozen=True, slots=True)
class ShoppingListAttachmentDto:
    attachment_id: UUID
    sequence: int


@dataclass(frozen=True, slots=True)
class InferredSuggestionDto:
    """One "Dora thinks you're out of this" suggestion. `reason` is the belief's
    own plain-English why, so the chip can explain itself on tap."""
    stock_item_id: UUID
    name: str
    reason: str


@dataclass(frozen=True, slots=True)
class ShoppingListDetailDto:
    shopping_list_id: UUID
    # Custom name (None = self-labelled) + the resolved label to render —
    # same split as the summaries DTO; the fallback rule lives on the entity.
    name: str | None
    display_name: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    totals: ShoppingListTotalsDto
    planned_shop_date: date | None = None
    lines: List[ShoppingListLineDto] = field(default_factory=list)
    # empty list when the list is a draft or has no attachments yet.
    attachments: List[ShoppingListAttachmentDto] = field(default_factory=list)
    # FU-653 — things Dora believes you've run out of that aren't on this list
    # yet. **Suggestions only**: nothing is added, no line is created, and the
    # list is identical whether or not you look at them (owner directive —
    # inference must not get in the way of the normal flow). Always empty when
    # the user hasn't opted the shopping surface in, and on a finished list
    # (suggesting additions to a completed shop is noise).
    inferred_suggestions: List['InferredSuggestionDto'] = field(default_factory=list)


class GetShoppingListDetailHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, shopping_list_id: UUID) -> ShoppingListDetailDto | None:
        _List: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if _List is None:
            return None

        _Lines: List[ShoppingListLine] = (
            self.repository.get(ShoppingListLine)
            .all(EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id))
        )
        _Lines.sort(key=lambda l: (l.sequence, l.id))

        # Pre-load all referenced stock items + their linked products in
        # bulk so we render N rows without N round-trips.
        # product-only lines have no stock_item_id; skip
        # those when assembling the stock-item id set.
        _StockItemIds = list({l.stock_item_id for l in _Lines if l.stock_item_id})
        _StockItems: dict[UUID, StockItem] = {}
        if _StockItemIds:
            _Loaded = (
                self.repository.get(StockItem)
                .include("stock_level")
                .include("stock_location")
                .include("products")
                    .then_include("store")
                .include("products")
                    .then_include("current_offer")
                .all(EntityField(StockItem, "id").in_(_StockItemIds))
            )
            _StockItems = {s.id: s for s in _Loaded}

        # bulk-load PreferredBuy labels for the lines' stock items so
        # each line can offer them as a hint picker without N round-trips.
        _PreferredBuysByItem: dict[UUID, List[PreferredBuy]] = {}
        if _StockItemIds:
            for pb in self.repository.get(PreferredBuy).all(
                EntityField(PreferredBuy, "stock_item_id").in_(_StockItemIds)
            ):
                _PreferredBuysByItem.setdefault(pb.stock_item_id, []).append(pb)

        # RD-18 — bulk-derive which of the lines' stock items have any
        # recorded substitute. StockItemSubstitute is undirected (canonical
        # a_id < b_id), so an item counts if it appears on either side.
        _ItemsWithSubs: set[UUID] = set()
        if _StockItemIds:
            from sqlalchemy import or_, select
            from dora_api.app import db
            _sub = db.metadata.tables["StockItemSubstitute"]
            _rows = db.session.execute(
                select(_sub.c.stock_item_a_id, _sub.c.stock_item_b_id).where(
                    or_(
                        _sub.c.stock_item_a_id.in_(_StockItemIds),
                        _sub.c.stock_item_b_id.in_(_StockItemIds),
                    )
                )
            ).all()
            _WantedKeys = {str(i) for i in _StockItemIds}
            for _a, _b in _rows:
                for _side in (_a, _b):
                    _key = str(UUID(bytes=_side)) if isinstance(_side, bytes) else str(_side)
                    if _key in _WantedKeys:
                        _ItemsWithSubs.add(_key)

        # bulk-load product names for product-only lines
        # so the DTO can fall back to the product name when there's
        # no anchor stock item to ask. Keep it minimal — just name +
        # id; the offers list comes from the linked-stock-item path
        # when the line has both anchors.
        _ProductIds = list({l.product_id for l in _Lines if l.product_id})
        _ProductNames: dict[UUID, str] = {}
        if _ProductIds:
            _LoadedProducts = (
                self.repository.get(Product)
                .all(EntityField(Product, "id").in_(_ProductIds))
            )
            _ProductNames = {p.id: p.name for p in _LoadedProducts}

        # Location lookup powers the per-line breadcrumb used to group lines
        # by shopper's route through the store. Loaded once and walked
        # locally so we don't do per-line ancestry queries.
        _LocationLookup: dict[UUID, StockLocation] = {}
        if any(s.stock_location is not None for s in _StockItems.values()):
            _LocationLookup = {
                loc.id: loc for loc in self.repository.get(StockLocation).all()
            }

        # Resolve store names for any `purchased_store_id` overrides
        # so the line DTO can render the chip without a second round-trip.
        _StoreNameLookup: dict[UUID, str] = {}
        _PurchasedStoreIds = {
            l.purchased_store_id for l in _Lines if l.purchased_store_id
        }
        if _PurchasedStoreIds:
            stores = self.repository.get(Store).all(
                EntityField(Store, "id").in_(list(_PurchasedStoreIds))
            )
            _StoreNameLookup = {s.id: s.name for s in stores}

        # per-item prefill source: the most-recent
        # *actual purchase* of each stock item on a prior finished list, priced
        # via the shared actual→picked ladder. This is the honest per-item
        # number for the till editor; manual price observations are per-measure
        # (per-L/kg) and feed the "Your prices" widget, not this per-item field.
        _PriorPurchaseByItem: dict[UUID, tuple[datetime, float]] = {}
        if _StockItemIds:
            _PriorLines = self.repository.get(ShoppingListLine).all(
                EntityField(ShoppingListLine, ShoppingListLine.Fields.STOCK_ITEM_ID).in_(_StockItemIds)
                & EntityField(ShoppingListLine, ShoppingListLine.Fields.IS_TICKED).eq(True)
            )
            # Exclude the list being viewed (compare as str — the path param
            # may arrive as a string while the FK is a UUID).
            _CurrentId = str(shopping_list_id)
            _PriorListIds = {
                l.shopping_list_id for l in _PriorLines
                if str(l.shopping_list_id) != _CurrentId
            }
            _DoneCompletedAt: dict[UUID, datetime] = {}
            if _PriorListIds:
                for sl in self.repository.get(ShoppingList).all(
                    EntityField(ShoppingList, "id").in_(list(_PriorListIds))
                ):
                    if sl.is_done:
                        _DoneCompletedAt[sl.id] = sl.completed_at or sl.created_at
            for l in _PriorLines:
                completed = _DoneCompletedAt.get(l.shopping_list_id)
                if completed is None:
                    continue
                paid = line_paid_unit_price(l)
                if paid is None:
                    continue
                prev = _PriorPurchaseByItem.get(l.stock_item_id)
                if prev is None or completed > prev[0]:
                    _PriorPurchaseByItem[l.stock_item_id] = (completed, paid)

        def _breadcrumb_for(item: StockItem | None) -> List[str]:
            if item is None or item.stock_location is None:
                return []
            crumbs: List[str] = []
            cursor: StockLocation | None = item.stock_location
            safety = 16
            while cursor is not None and safety > 0:
                crumbs.append(cursor.name)
                cursor = (
                    _LocationLookup.get(cursor.parent_id) if cursor.parent_id else None
                )
                safety -= 1
            crumbs.reverse()
            return crumbs

        _LineDtos: List[ShoppingListLineDto] = []
        for line in _Lines:
            item = _StockItems.get(line.stock_item_id) if line.stock_item_id else None
            offers: List[LineProductOfferDto] = []
            if item is not None:
                for product in item.products or []:
                    offers.append(LineProductOfferDto(
                        product_id = product.id,
                        name = product.name,
                        brand = product.brand,
                        store_id = product.store.id,
                        store_name = product.store.name,
                        size = product.size,
                        price_now = product.current_offer.price_now if product.current_offer else None,
                        price_was = product.current_offer.price_was if product.current_offer else None,
                        is_selected = line.selected_product_id == product.id,
                    ))
                # Sort offers: cheapest first, then alphabetical by store.
                offers.sort(key=lambda o: (
                    o.price_now if o.price_now is not None else float("inf"),
                    o.store_name.lower(),
                ))
            # fall back to the product name for
            # product-only lines (no anchor stock item to ask).
            _line_display_name = (
                item.name if item
                else (_ProductNames.get(line.product_id, "(missing item)")
                      if line.product_id else "(missing item)")
            )
            # D3 prefill: prior actual purchase (per-item) wins; else the
            # line's chosen offer (selected, else cheapest). Source-labelled.
            _prefill_price: float | None = None
            _prefill_label: str | None = None
            _prior = (
                _PriorPurchaseByItem.get(line.stock_item_id)
                if line.stock_item_id else None
            )
            if _prior is not None:
                _prefill_price = _prior[1]
                _prefill_label = "from your last receipt"
            else:
                _chosen = next(
                    (o for o in offers if o.is_selected),
                    offers[0] if offers else None,
                )
                if _chosen is not None and _chosen.price_now is not None:
                    _prefill_price = _chosen.price_now
                    _prefill_label = f"from {_chosen.store_name} offer"
            _LineDtos.append(ShoppingListLineDto(
                line_id = line.id,
                stock_item_id = line.stock_item_id,
                product_id = line.product_id,
                stock_item_name = _line_display_name,
                stock_level_name = (
                    item.stock_level.name if item and item.stock_level else None
                ),
                stock_location_id = (
                    item.stock_location.id if item and item.stock_location else None
                ),
                stock_location_breadcrumb = _breadcrumb_for(item),
                quantity = line.quantity,
                is_ticked = bool(line.is_ticked),
                selected_product_id = line.selected_product_id,
                sequence = line.sequence,
                added_via = line.added_via,
                added_at = line.added_at,
                deferred_by_budget = bool(line.deferred_by_budget),
                deferred_reason = line.deferred_reason,
                actual_unit_price = line.actual_unit_price,
                purchased_store_id = line.purchased_store_id,
                purchased_store_name = (
                    _StoreNameLookup.get(line.purchased_store_id)
                    if line.purchased_store_id else None
                ),
                prefill_unit_price = _prefill_price,
                prefill_source_label = _prefill_label,
                offers = offers,
                preferred_buy_id = line.preferred_buy_id,
                preferred_buys = sorted(
                    (
                        LinePreferredBuyDto(preferred_buy_id = pb.id, label = pb.label)
                        for pb in _PreferredBuysByItem.get(line.stock_item_id, [])
                    ),
                    key=lambda d: d.label.lower(),
                ),
                has_substitutes = (
                    str(line.stock_item_id) in _ItemsWithSubs
                    if line.stock_item_id else False
                ),
            ))

        # receipt-photo metadata. Only fetched for non-draft lists
        # (the UI hides the section on drafts anyway; saves a query for
        # the common case).
        _Attachments: List[ShoppingListAttachmentDto] = []
        if _List.status != "draft":
            _Attachments = [
                ShoppingListAttachmentDto(
                    attachment_id=row["id"], sequence=row["sequence"],
                )
                for row in get_attachment_metadata_for_list(_List.id)
            ]

        return ShoppingListDetailDto(
            inferred_suggestions = self._inferred_suggestions(_List, _Lines),
            shopping_list_id = _List.id,
            name = _List.name,
            display_name = _List.display_name,
            status = _List.status,
            created_at = _List.created_at,
            completed_at = _List.completed_at,
            planned_shop_date = _List.planned_shop_date,
            totals = compute_list_totals(_LineDtos),
            lines = _LineDtos,
            attachments = _Attachments,
        )


    # FU-653 — the shopping surface of the Zero-Input belief overlay.
    _MAX_SUGGESTIONS = 6

    def _inferred_suggestions(
        self, shopping_list: ShoppingList, lines: List[ShoppingListLine],
    ) -> List[InferredSuggestionDto]:
        """Items Dora believes are out, that this list doesn't already carry.

        Scoped to items *recorded* as available — an item you've already
        recorded as out is the existing low-stock machinery's job (auto-add,
        the Needs-restock filter), and repeating it here as a "suggestion"
        would be Dora taking credit for what you told her.

        Capped: this is a nudge beside the list, not a second list. Sorted by
        name so the order is stable between refreshes rather than shuffling
        with belief confidence.
        """
        if shopping_list.is_done:
            return []
        already_on_list = {l.stock_item_id for l in lines if l.stock_item_id}
        candidates = (
            self.repository.get(StockItem).include("stock_level").all()
        )
        candidates = [c for c in candidates if c.id not in already_on_list]
        divergence = resolve_divergence(self.repository, SURFACE_SHOPPING, candidates)
        if not divergence.believed_out:
            return []
        by_id = {c.id: c for c in candidates}
        out = [
            InferredSuggestionDto(
                stock_item_id = item_id,
                name = by_id[item_id].name,
                reason = divergence.reasons.get(item_id, ""),
            )
            for item_id in divergence.believed_out
            if item_id in by_id
        ]
        out.sort(key=lambda s: s.name.lower())
        return out[:self._MAX_SUGGESTIONS]


@SHOPPING_LIST_ROUTER.route("/<uuid:shopping_list_id>", methods=["GET"])
def get_shopping_list_detail(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Detail = GetShoppingListDetailHandler(SqlAlchemyRepository()).handle(shopping_list_id)
    if _Detail is None:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.debug(
        "Shopping list %s detail: %d lines", shopping_list_id, len(_Detail.lines)
    )
    return ok(_Detail)
