import random
import string
import uuid

from application.services.ipersistence_context import IPersistenceContext
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


async def seed_initial_data_async(persistence: IPersistenceContext):
    stock_location_one = generate_entity(StockLocation)
    persistence.add(stock_location_one)

    stock_level_high = generate_entity(StockLevel)
    stock_level_high.description = "High"
    stock_level_medium = generate_entity(StockLevel)
    stock_level_medium.description = "Medium"
    stock_level_low = generate_entity(StockLevel)
    stock_level_low.description = "Low"
    persistence.add(stock_level_high)
    persistence.add(stock_level_medium)
    persistence.add(stock_level_low)

    stock_item_one = generate_entity(StockItem)
    stock_item_one.location = stock_location_one
    stock_item_one.stock_level = stock_level_medium
    persistence.add(stock_item_one)

    await persistence.save_changes_async()

def generate_entity(entity_type):
    data = {}
    for attribute in entity_type.__annotations__.items():
        data[attribute[0]] = get_value_for_type(attribute[1])
    return entity_type(**data)

def get_value_for_type(type):
    if type == uuid:
        return uuid.uuid4()

    if type == str:
        return ''.join(random.choices(string.ascii_letters, k=15))

    return None
