import datetime
import random
import string
from typing import get_origin
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
    #session.add_all([x, y, z])

    stock_item_one = generate_entity(StockItem)
    stock_item_one.location = stock_location_one
    stock_item_one.stock_level = stock_level_medium
    persistence.add(stock_item_one)

    stock_item_two = generate_entity(StockItem)
    stock_item_two.location = stock_location_one
    stock_item_two.stock_level = stock_level_medium
    persistence.add(stock_item_two)

    await persistence.save_changes_async()

def is_entity(attribute_type):
        if get_origin(attribute_type) == list:
            attribute_type = attribute_type.__args__[0]
        return hasattr(attribute_type, "__module__") and "entities" in attribute_type.__module__

def generate_entity(entity_type):
    data = {}
    for attribute in entity_type.__annotations__.items():
        data[attribute[0]] = get_value_for_type(entity_type, attribute[0], attribute[1])
    return entity_type(**data)

def get_value_for_type(entity_type, attr_name, type):
    if is_entity(type):
        return generate_entity(type)

    if type == uuid:
        return uuid.uuid4()

    if type == str:
        return ''.join([entity_type.__name__, "__", attr_name, '__'] + random.choices(string.ascii_letters, k=5))

    if type == datetime:
        start_date = datetime.datetime.now() - datetime.timedelta(days=500)
        end_date = datetime.datetime.now() + datetime.timedelta(days=500)
        return start_date + (end_date - start_date) * random.random()

    raise Exception(f"Could not generate value, unsupported type: {type}")
