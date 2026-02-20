from dataclasses import dataclass
from datetime import datetime

from domain.entities.base_entity import BaseEntity
from domain.entities.stock_group import StockGroup
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


@dataclass(slots=True)
class StockItem(BaseEntity):
    days_until_stocktake_alert: int
    image: bytes | None
    name: str
    notes: str | None
    # products: List[Product]
    stock_group: StockGroup | None
    stock_level_last_updated: datetime
    stock_level: StockLevel
    stock_location: StockLocation | None
    stocktake_alerts_are_enabled: bool
