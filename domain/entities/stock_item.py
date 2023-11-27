from dataclasses import dataclass
from datetime import datetime
from domain.entities.base_entity import BaseEntity

from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


@dataclass
class StockItem(BaseEntity):
    location: StockLocation = None
    name: str = None
    # products: List[Product] = None
    stock_level: StockLevel = None
    stock_level_last_updated: datetime = None
