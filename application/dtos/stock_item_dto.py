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

def breadth_first_traversal(dictionary):
    if not isinstance(dictionary, dict):
        raise ValueError("Input must be a dictionary")

    queue = [dictionary]

    while queue:
        current_dict = queue.pop(0)
        keys = current_dict.keys()

        for key in keys:
            value = current_dict[key]
            print(f"Key: {key}, Value: {value}")

            if isinstance(value, dict):
                queue.append(value)

# Example usage
nested_dict = {
    'a': {
        'b': {
            'c': {
                'd': 1
            }
        },
        'e': 2
    },
    'f': {
        'g': 3
    }
}



if __name__ == "__main__":
    breadth_first_traversal(nested_dict)
    x = get_stock_item_dto(StockItem(uuid.uuid4()))
    v= 0

# TODO: Look into tests to check all entity classes have an import statement in the __init__.py file, could use inspect.getsourcefile or something
