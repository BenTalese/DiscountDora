from dataclasses import dataclass
from datetime import datetime
from typing import List

from domain.entities.base_entity import BaseEntity
from domain.entities.product import Product
from domain.entities.stock_group import StockGroup
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


@dataclass
class StockItem(BaseEntity):
    days_until_stocktake_alert: int = None
    image: bytes = None
    name: str = None
    notes: str = None
    products: List[Product] = None
    stock_group: StockGroup = None
    stock_level_last_updated: datetime = None
    stock_level: StockLevel = None
    stock_location: StockLocation = None
    stocktake_alerts_are_enabled: bool = None
