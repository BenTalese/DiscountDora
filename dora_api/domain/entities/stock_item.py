from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation


@dataclass
class StockItem(BaseEntity):
    days_until_stocktake_alert: int
    image: bytes | None
    name: str
    notes: str | None
    stock_group: StockGroup | None
    stock_level_last_updated: datetime
    stock_level: StockLevel
    stock_location: StockLocation | None
    stocktake_alerts_are_enabled: bool
    expiry_date: date | None = None
    is_flagged: bool = False
    # When True, transitioning this item to Low or Out of stock auto-adds it
    # to the primary shopping list. Independent of `is_flagged` — that one
    # drives auto-generate and severity weighting on alerts, this one is
    # the "always restock" preference.
    auto_add_when_low: bool = False
    # "I've cracked open the jar" — true while the item is being actively
    # consumed. `opened_on` is set automatically when `is_open` flips to
    # True; flipping back to False clears it.
    is_open: bool = False
    opened_on: date | None = None
    # X1: distinct from stock_level_last_updated. A "check" is the user
    # confirming the current level is correct without changing it.
    # Updating the level updates BOTH timestamps; clicking "Still
    # correct" in stocktake mode only moves this one. None = never
    # checked (treated as maximally overdue by the stocktake queue).
    last_checked_at: datetime | None = None
    # Merchant products linked to this stock item, used by the product-search
    # flow to surface deals and by the detail view to show "what merchant
    # SKUs are tracked here". Default empty so callers that don't care about
    # the m2m don't have to pass it.
    products: List[Product] = field(default_factory=list)
    # NOTE: substitutes are a self-referential m2m stored in the
    # StockItemSubstitute table and accessed directly (the generic repository
    # can't self-join an entity to itself), so there's no relationship field
    # here. See features/stock_items/add_substitute.py and get_stock_item_detail.

    class Fields(BaseEntity.Fields):
        AUTO_ADD_WHEN_LOW = "auto_add_when_low"
        DAYS_UNTIL_STOCKTAKE_ALERT = "days_until_stocktake_alert"
        EXPIRY_DATE = "expiry_date"
        IMAGE = "image"
        IS_FLAGGED = "is_flagged"
        IS_OPEN = "is_open"
        NAME = "name"
        NOTES = "notes"
        OPENED_ON = "opened_on"
        PRODUCTS = "products"
        STOCK_GROUP = "stock_group"
        STOCK_LEVEL = "stock_level"
        STOCK_LEVEL_LAST_UPDATED = "stock_level_last_updated"
        STOCK_LOCATION = "stock_location"
        STOCKTAKE_ALERTS_ARE_ENABLED = "stocktake_alerts_are_enabled"
        LAST_CHECKED_AT = "last_checked_at"
