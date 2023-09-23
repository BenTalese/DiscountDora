from application.dtos.stock_item_dto import StockItemDto
from application.dtos.stock_location_dto import StockLocationDto
from domain.entities.stock_item import StockItem
from domain.entities.stock_location import StockLocation


def get_stock_item_dto(stock_item: StockItem) -> StockItemDto:
    dto = StockItemDto()
    dto.name = stock_item.name
    dto.stock_item_id = stock_item.id
    dto.stock_level_id = stock_item.stock_level.id
    dto.stock_location_id = stock_item.location.id if stock_item.location else None
    dto.stock_level_last_updated_on_utc = stock_item.stock_level_last_updated_on_utc
    return dto

def get_stock_location_dto(stock_location: StockLocation) -> StockLocationDto:
    dto = StockLocationDto()
    dto.description = stock_location.description
    dto.stock_location_id = stock_location.id
    return dto

# TODO: No tests to check if all properties are mapped
# TODO: Look into tests to check all dto classes have an import statement in the __init__.py file, could use inspect.getsourcefile or something
