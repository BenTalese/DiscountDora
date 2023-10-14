import datetime
from dataclasses import dataclass

from domain.entities.stock_item import StockItem


@dataclass
class StockItemDto:
    dto_name: str
    dto_stock_item_id: uuid
    dto_stock_level_id: uuid
    dto_stock_location: StockLocationDto
    dto_stock_level_last_updated_on_utc: datetime

def get_stock_item_dto(stock_item: StockItem) -> StockItemDto:
    return StockItemDto(
        name = stock_item.name,
        stock_item_id = stock_item.id,
        stock_level_id = stock_item.stock_level.id if stock_item.stock_level else None,
        stock_location_id = stock_item.location.id if stock_item.location else None,
        stock_level_last_updated_on_utc = stock_item.stock_level_last_updated_on_utc
    )
