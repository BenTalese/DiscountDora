from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.entities.stock_item import StockItem


@dataclass
class StockItemViewModel:
    name: str
    stock_item_id: UUID
    stock_level_id: UUID
    stock_location_id: UUID
    stock_level_last_updated: datetime


def get_stock_item_view_model(stock_item: StockItem) -> StockItemViewModel:
    return StockItemViewModel(
        name = stock_item.name,
        stock_item_id = stock_item.id.value,
        stock_level_id = stock_item.stock_level.id.value if stock_item.stock_level else None,
        stock_location_id = stock_item.stock_location.id.value if stock_item.stock_location else None,
        stock_level_last_updated = stock_item.stock_level_last_updated
    )
