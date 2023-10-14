from dataclasses import dataclass
import datetime
import uuid

from application.dtos.stock_item_dto import StockItemDto
from application.dtos.stock_location_dto import StockLocationDto

@dataclass
class StockLocationViewModel:
    viewmodel_location_description: str

@dataclass
class StockItemViewModel:
    name: str
    stock_item_id: uuid
    stock_level_id: uuid
    stock_location_id: uuid
    stock_level_last_updated_on_utc: datetime

def get_stock_location_view_model(stock_location: StockLocationDto) -> StockLocationViewModel:
    return StockLocationViewModel(
        viewmodel_location_description = stock_location.description
    )

def get_stock_item_view_model(stock_item: StockItemDto) -> StockItemViewModel:
    return StockItemViewModel(
        name = stock_item.name,
        stock_item_id = stock_item.stock_item_id.value if stock_item.stock_item_id else None,
        stock_level_id = stock_item.stock_level_id.value if stock_item.stock_level_id else None,
        stock_location_id = stock_item.stock_location_id.value if stock_item.stock_location_id else None,
        stock_level_last_updated_on_utc = stock_item.stock_level_last_updated_on_utc
    )
