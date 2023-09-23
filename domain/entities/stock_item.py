from dataclasses import dataclass
import datetime
import uuid

from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


@dataclass
class StockItem:
    id: uuid = None
    location: StockLocation = None
    name: str = None
    stock_level: StockLevel = None
    stock_level_last_updated_on_utc: datetime = None
