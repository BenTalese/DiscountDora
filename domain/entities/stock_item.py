import datetime
import uuid

from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


class StockItem:
    id: uuid
    location: StockLocation
    name: str
    stock_level: StockLevel
    stock_level_last_updated_on_utc: datetime
