from dataclasses import dataclass
import datetime
from domain.entities.base_entity import BaseEntity

from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


@dataclass
class StockItem(BaseEntity):
    location: StockLocation = None
    name: str = None
    stock_level: StockLevel = None
    stock_level_last_updated_on_utc: datetime = None
