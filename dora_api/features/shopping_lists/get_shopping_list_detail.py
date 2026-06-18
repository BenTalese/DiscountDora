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
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


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


# FU-215 — a stock item's PreferredBuy label as a pickable shopping hint.
@dataclass(frozen=True, slots=True)
class LinePreferredBuyDto:
    preferred_buy_id: UUID
    label: str


@dataclass(frozen=True, slots=True)
class ShoppingListLineDto:
    line_id: UUID
    # C-7 Chunk 3 — a line is anchored by stock_item_id OR product_id
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
    # P2-02 purchase memory — what the shopper actually paid / where they
    # actually bought it. Both NULL until the user overrides on the line.
    actual_unit_price: float | None
    purchased_store_id: UUID | None
    purchased_store_name: str | None
    offers: List[LineProductOfferDto] = field(default_factory=list)
    # FU-215 — the chosen hint + the item's available labels for the picker.
    preferred_buy_id: UUID | None = None
    preferred_buys: List[LinePreferredBuyDto] = field(default_factory=list)


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
    for the dashboard's primary-list stats (it reads these instead of summing)."""
    total_price = 0.0
    remaining_price = 0.0
    total_savings = 0.0
    unticked = 0
    for line in lines:
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
        ticked_count = len(lines) - unticked,
        line_count = len(lines),
    )


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


class GetShoppingListDetailHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

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
        # C-7 Chunk 3 — product-only lines have no stock_item_id; skip
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

        # FU-215 — bulk-load PreferredBuy labels for the lines' stock items so
        # each line can offer them as a hint picker without N round-trips.
        _PreferredBuysByItem: dict[UUID, List[PreferredBuy]] = {}
        if _StockItemIds:
            for pb in self.repository.get(PreferredBuy).all(
                EntityField(PreferredBuy, "stock_item_id").in_(_StockItemIds)
            ):
                _PreferredBuysByItem.setdefault(pb.stock_item_id, []).append(pb)

        # C-7 Chunk 3 — bulk-load product names for product-only lines
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
            # C-7 Chunk 3 — fall back to the product name for
            # product-only lines (no anchor stock item to ask).
            _line_display_name = (
                item.name if item
                else (_ProductNames.get(line.product_id, "(missing item)")
                      if line.product_id else "(missing item)")
            )
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
                actual_unit_price = line.actual_unit_price,
                purchased_store_id = line.purchased_store_id,
                purchased_store_name = (
                    _StoreNameLookup.get(line.purchased_store_id)
                    if line.purchased_store_id else None
                ),
                offers = offers,
                preferred_buy_id = line.preferred_buy_id,
                preferred_buys = sorted(
                    (
                        LinePreferredBuyDto(preferred_buy_id = pb.id, label = pb.label)
                        for pb in _PreferredBuysByItem.get(line.stock_item_id, [])
                    ),
                    key=lambda d: d.label.lower(),
                ),
            ))

        return ShoppingListDetailDto(
            shopping_list_id = _List.id,
            name = _List.name,
            display_name = _List.display_name,
            status = _List.status,
            created_at = _List.created_at,
            completed_at = _List.completed_at,
            planned_shop_date = _List.planned_shop_date,
            totals = compute_list_totals(_LineDtos),
            lines = _LineDtos,
        )


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>", methods=["GET"])
def get_shopping_list_detail(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Detail = get_container().inject(GetShoppingListDetailHandler).handle(shopping_list_id)
    if _Detail is None:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.debug(
        "Shopping list %s detail: %d lines", shopping_list_id, len(_Detail.lines)
    )
    return ok(_Detail)
