"""GET /api/shopping-lists/<id> — full detail with lines + linked products.

Each line carries enough info to render the row without further fetches:
stock item name + level, selected offer (if chosen) and *all* offers (so the
user can pick), and current ticked/quantity state. Totals are computed
client-side from the offers so we don't have to round-trip on tick.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID

from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.shopping_list import (ShoppingList,
                                                    ShoppingListLine)
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
    merchant_id: UUID
    merchant_name: str
    size: str | None
    price_now: float | None
    price_was: float | None
    is_selected: bool
    is_preferred: bool


@dataclass(frozen=True, slots=True)
class ShoppingListLineDto:
    line_id: UUID
    stock_item_id: UUID
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
    purchased_merchant_id: UUID | None
    purchased_merchant_name: str | None
    offers: List[LineProductOfferDto] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ShoppingListDetailDto:
    shopping_list_id: UUID
    name: str
    is_primary: bool
    is_archived: bool
    is_in_progress: bool
    created_at: datetime
    completed_at: datetime | None
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
        _StockItemIds = list({l.stock_item_id for l in _Lines})
        _StockItems: dict[UUID, StockItem] = {}
        if _StockItemIds:
            _Loaded = (
                self.repository.get(StockItem)
                .include("stock_level")
                .include("stock_location")
                .include("products")
                    .then_include("merchant")
                .include("products")
                    .then_include("current_offer")
                .all(EntityField(StockItem, "id").in_(_StockItemIds))
            )
            _StockItems = {s.id: s for s in _Loaded}

        # Location lookup powers the per-line breadcrumb used to group lines
        # by shopper's route through the store. Loaded once and walked
        # locally so we don't do per-line ancestry queries.
        _LocationLookup: dict[UUID, StockLocation] = {}
        if any(s.stock_location is not None for s in _StockItems.values()):
            _LocationLookup = {
                loc.id: loc for loc in self.repository.get(StockLocation).all()
            }

        # Resolve merchant names for any `purchased_merchant_id` overrides
        # so the line DTO can render the chip without a second round-trip.
        _MerchantNameLookup: dict[UUID, str] = {}
        _PurchasedMerchantIds = {
            l.purchased_merchant_id for l in _Lines if l.purchased_merchant_id
        }
        if _PurchasedMerchantIds:
            merchants = self.repository.get(Merchant).all(
                EntityField(Merchant, "id").in_(list(_PurchasedMerchantIds))
            )
            _MerchantNameLookup = {m.id: m.name for m in merchants}

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
            item = _StockItems.get(line.stock_item_id)
            offers: List[LineProductOfferDto] = []
            preferred_id: UUID | None = item.preferred_product_id if item else None
            if item is not None:
                for product in item.products or []:
                    offers.append(LineProductOfferDto(
                        product_id = product.id,
                        name = product.name,
                        brand = product.brand,
                        merchant_id = product.merchant.id,
                        merchant_name = product.merchant.name,
                        size = product.size,
                        price_now = product.current_offer.price_now if product.current_offer else None,
                        price_was = product.current_offer.price_was if product.current_offer else None,
                        is_selected = line.selected_product_id == product.id,
                        is_preferred = preferred_id is not None and preferred_id == product.id,
                    ))
                # Sort offers: preferred merchant first, then cheapest, then
                # alphabetical. The picker shows preferred up top because the
                # user has explicitly marked it; cheapest is the next-best
                # tiebreak.
                offers.sort(key=lambda o: (
                    0 if o.is_preferred else 1,
                    o.price_now if o.price_now is not None else float("inf"),
                    o.merchant_name.lower(),
                ))
            _LineDtos.append(ShoppingListLineDto(
                line_id = line.id,
                stock_item_id = line.stock_item_id,
                stock_item_name = item.name if item else "(missing item)",
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
                purchased_merchant_id = line.purchased_merchant_id,
                purchased_merchant_name = (
                    _MerchantNameLookup.get(line.purchased_merchant_id)
                    if line.purchased_merchant_id else None
                ),
                offers = offers,
            ))

        return ShoppingListDetailDto(
            shopping_list_id = _List.id,
            name = _List.name,
            is_primary = bool(_List.is_primary),
            is_archived = bool(_List.is_archived),
            is_in_progress = bool(_List.is_in_progress),
            created_at = _List.created_at,
            completed_at = _List.completed_at,
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
