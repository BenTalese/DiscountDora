import datetime
import os
import sys
import uuid
from dataclasses import dataclass

sys.path.append(os.getcwd())
from application.dtos.stock_location_dto import StockLocationDto
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
        dto_name = stock_item.name.isdigit(),
        dto_stock_item_id = stock_item.id,
        dto_stock_level_id = stock_item.stock_level.id if stock_item.stock_level else None,
        dto_stock_location = stock_item.location,
        dto_stock_level_last_updated_on_utc = stock_item.stock_level_last_updated_on_utc
    )

if __name__ == "__main__":
    x = get_stock_item_dto(StockItem(uuid.uuid4()))
    v= 0

# TODO: Look into tests to check all entity classes have an import statement in the __init__.py file, could use inspect.getsourcefile or something
