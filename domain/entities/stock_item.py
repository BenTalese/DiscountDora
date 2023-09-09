import datetime
import uuid

from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


class StockItem:
    def __init__(
            self,
            id: uuid,
            location: StockLocation,
            name: str,
            stock_level: StockLevel,
            stock_level_last_updated_on_utc: datetime):
        self.id = id
        self.location = location
        self.name = name
        self.stock_level = stock_level
        self.stock_level_last_updated_on_utc = stock_level_last_updated_on_utc
