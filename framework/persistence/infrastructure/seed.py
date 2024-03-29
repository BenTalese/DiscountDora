from datetime import datetime, timedelta
import random
import string

from application.services.ipersistence_context import IPersistenceContext
from domain.entities.merchant import Merchant
from domain.entities.shopping_list import ShoppingList
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation
from domain.entities.user import User
from framework.persistence.infrastructure.persistence_helper_methods import is_entity, is_list


async def seed_initial_data_async(persistence: IPersistenceContext):
    # TODO: Find a place for system controlled data such as merchants
    merchant_one = generate_entity(Merchant)
    merchant_one.name = "Woolworths"
    merchant_two = generate_entity(Merchant)
    merchant_two.name = "Coles"
    persistence.add(merchant_one)
    persistence.add(merchant_two)

    # TEST DATA:
    user = generate_entity(User)
    user.send_deals_on_day = datetime.now().weekday()
    user.email = "ben.talese@gmail.com"
    persistence.add(user)

    stock_location_one = generate_entity(StockLocation)
    persistence.add(stock_location_one)

    stock_level_one = generate_entity(StockLevel)
    stock_level_one.description = "Well-Stocked"
    stock_level_two = generate_entity(StockLevel)
    stock_level_two.description = "Low Stock"
    stock_level_three = generate_entity(StockLevel)
    stock_level_three.description = "Out of Stock"
    persistence.add(stock_level_one)
    persistence.add(stock_level_two)
    persistence.add(stock_level_three)
    #session.add_all([x, y, z])
    # TODO: add(*entities) (actually, why?...for this one file?)

    stock_item_one = generate_entity(StockItem)
    stock_item_one.stock_location = stock_location_one
    stock_item_one.stock_level = stock_level_one
    persistence.add(stock_item_one)

    stock_item_two = generate_entity(StockItem)
    stock_item_two.stock_location = stock_location_one
    stock_item_two.stock_level = stock_level_two
    persistence.add(stock_item_two)
    persistence.add(stock_item_one)

    stock_item_three = generate_entity(StockItem)
    stock_item_three.stock_location = stock_location_one
    stock_item_three.stock_level = stock_level_three
    persistence.add(stock_item_three)

    shopping_list_one = generate_entity(ShoppingList)
    shopping_list_one.items.append(stock_item_one)
    shopping_list_one.items.append(stock_item_two)
    persistence.add(shopping_list_one)

    await persistence.save_changes_async()

def generate_entity(entity_type):
    data = {}
    for attribute_name, attribute_type in entity_type.__annotations__.items():
        data[attribute_name] = get_value_for_type(entity_type, attribute_name, attribute_type)
    return entity_type(**data)

def get_value_for_type(entity_type, attr_name, type):
    if is_list(type):
        return [get_value_for_type(entity_type, attr_name, type.__args__[0])]

    if is_entity(type):
        return generate_entity(type)

    if type == str:
        return ''.join([entity_type.__name__, "__", attr_name, '__'] + random.choices(string.ascii_letters, k=5))

    if type == datetime:
        start_date = datetime.now() - timedelta(days=2000)
        end_date = datetime.now() + timedelta(days=2000)
        return start_date + (end_date - start_date) * random.random()

    return type()
