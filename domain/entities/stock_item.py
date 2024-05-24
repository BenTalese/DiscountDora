from dataclasses import dataclass
from datetime import datetime

from domain.entities.base_entity import BaseEntity
from domain.entities.stock_group import StockGroup
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


@dataclass
class StockItem(BaseEntity):
    days_until_stocktake_alert: int = None # TODO: have a global fallback option if this is 0
    # TODO: doracode (barcode to scan)
    image: bytes = None
    # TODO (maybe???): is_active/is_archived
    name: str = None
    notes: str = None
    # preferred_merchant: Merchant = None # TODO: (options: cheapest unit price, cheapest total price, woolies, coles, iga, instock?) (none means cheapest???)
    # products: List[Product] = None
    stock_group: StockGroup = None
    stock_level: StockLevel = None
    stock_level_last_updated: datetime = None
    stock_location: StockLocation = None
