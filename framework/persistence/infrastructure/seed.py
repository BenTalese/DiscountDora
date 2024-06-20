import random
import string
from datetime import datetime, timedelta

from application.services.ipersistence_context import IPersistenceContext
from domain.entities.merchant import Merchant
from domain.entities.product import Product
from domain.entities.shopping_list import ShoppingList
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation
from domain.entities.user import User
from framework.persistence.infrastructure.persistence_helper_methods import (
    is_entity, is_list)


async def seed_initial_data_async(persistence: IPersistenceContext):
    merchant_one = generate_entity(Merchant)
    merchant_one.name = "Woolworths"
    merchant_two = generate_entity(Merchant)
    merchant_two.name = "Coles"
    persistence.add(merchant_one)
    persistence.add(merchant_two)

    product_one = generate_entity(Product, True)
    product_one.is_active = True
    product_one.is_available = True
    product_one.merchant = merchant_one
    product_one.merchant_stockcode = "51741"
    product_one.name = "Cadbury Freddo Cake"
    product_one.size = "1.5L"
    product_one.size_unit = "L"
    product_one.size_value = 1.0
    product_one.web_url = "https://www.woolworths.com.au/shop/productdetails/51741"

    product_two = generate_entity(Product, True)
    product_two.is_active = True
    product_two.is_available = True
    product_two.merchant = merchant_two
    product_two.merchant_stockcode = "3056737"
    product_two.name = "Betty Crocker Gluten Free Vanilla Cupcake Mix"
    product_two.size = "460G"
    product_two.size_unit = "G"
    product_two.size_value = 460.0
    product_two.web_url = "https://www.coles.com.au/product/3056737"

    persistence.add(product_one)
    persistence.add(product_two)

    user = generate_entity(User)
    user.send_deals_on_day = datetime.now().weekday()
    user.email = "ben.talese@gmail.com"
    persistence.add(user)

    stock_location_one = generate_entity(StockLocation)
    persistence.add(stock_location_one)

    stock_level_one = StockLevel(name = "Well-Stocked", sequence = 0)
    stock_level_two = StockLevel(name = "Sufficient Stock", sequence = 1)
    stock_level_three = StockLevel(name = "Low Stock", sequence = 2)
    stock_level_four = StockLevel(name = "Out of Stock", sequence = 3)

    persistence.add(stock_level_one)
    persistence.add(stock_level_two)
    persistence.add(stock_level_three)
    persistence.add(stock_level_four)

    stock_item_one = generate_entity(StockItem)
    stock_item_one.products.append(product_one)
    stock_item_one.stock_location = stock_location_one
    stock_item_one.stock_level = stock_level_one
    persistence.add(stock_item_one)

    stock_item_two = generate_entity(StockItem)
    stock_item_two.products.append(product_two)
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

def generate_entity(entity_type, should_generate_navigations: bool = False):
    data = {}
    for attribute_name, attribute_type in entity_type.__annotations__.items():
        if is_entity(attribute_type) and should_generate_navigations or not is_entity(attribute_type):
            data[attribute_name] = get_value_for_type(entity_type, attribute_name, attribute_type, should_generate_navigations)

        if is_entity(attribute_type) and is_list(attribute_type) and not should_generate_navigations:
            data[attribute_name] = []

    return entity_type(**data)

def get_value_for_type(entity_type, attr_name, type, should_generate_navigations):
    if is_list(type):
        return [get_value_for_type(entity_type, attr_name, type.__args__[0], should_generate_navigations)]

    if is_entity(type) and should_generate_navigations:
        return generate_entity(type, should_generate_navigations)

    if type == str:
        return ''.join([entity_type.__name__, "__", attr_name, '__'] + random.choices(string.ascii_letters, k=5))

    if type == datetime:
        start_date = datetime.now() - timedelta(days=2000)
        end_date = datetime.now() + timedelta(days=2000)
        return start_date + (end_date - start_date) * random.random()

    return type()
