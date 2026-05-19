from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation


@dataclass
class StockItem(BaseEntity):
    DAYS_UNTIL_STOCKTAKE_ALERT = "days_until_stocktake_alert"
    days_until_stocktake_alert: int

    IMAGE = "image"
    image: bytes | None

    NAME = "name"
    name: str

    NOTES = "notes"
    notes: str | None

    STOCK_GROUP = "stock_group"
    stock_group: StockGroup | None

    STOCK_LEVEL = "stock_level"
    stock_level: StockLevel

    STOCK_LEVEL_LAST_UPDATED = "stock_level_last_updated"
    stock_level_last_updated: datetime

    STOCK_LOCATION = "stock_location"
    stock_location: StockLocation | None

    STOCKTAKE_ALERTS_ARE_ENABLED = "stocktake_alerts_are_enabled"
    stocktake_alerts_are_enabled: bool

    EXPIRY_DATE = "expiry_date"
    expiry_date: date | None = None

    IS_FLAGGED = "is_flagged"
    is_flagged: bool = False

    # Merchant products linked to this stock item, used by the product-search
    # flow to surface deals and by the detail view to show "what merchant
    # SKUs are tracked here". Default empty so callers that don't care about
    # the m2m don't have to pass it.
    PRODUCTS = "products"
    products: List[Product] = field(default_factory=list)
