from dataclasses import dataclass
from datetime import datetime

from domain.entities.base_entity import EntityID
from domain.entities.stock_item import StockItem


@dataclass
class StockItemDto:
    name: str
    stock_item_id: EntityID
    stock_level_id: EntityID
    stock_location_id: EntityID
    stock_level_last_updated: datetime

def get_stock_item_dto(stock_item: StockItem) -> StockItemDto:
    return StockItemDto(
        name = stock_item.name,
        stock_item_id = stock_item.id,
        stock_level_id = stock_item.stock_level.id if stock_item.stock_level else None,
        stock_location_id = stock_item.location.id if stock_item.location else None,
        stock_level_last_updated = stock_item.stock_level_last_updated
    )
