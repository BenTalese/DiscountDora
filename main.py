from typing import List, Any, Dict, Tuple
import requests
import json
from rich import print
import os

from examples import compare_offers, best_offers_by_merchant, generate_offer_table
from web_scraper import coles, woolies
from web_scraper.types import ProductOffers
from emailer.delivery import send_email

current_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(current_dir, 'secrets.json'), 'r') as file:
    SECRETS = json.load(file)

#TODO: Currently unavailable products come up as not found

def get_product_offers(product_names: List[str]) -> ProductOffers:
    """ Returns ProductOffers object with optimistic search results for product_names. """
    product_offers: Dict[str, List[Any]] = {}
    for name in product_names:
        product_offers[name] = []
        for merchant in [coles, woolies]:
            merchant_product_search = merchant.im_feeling_lucky(name)

            product = next(merchant_product_search, None)
            if (product is not None):
                product_offers[name].append(product)

        if not product_offers[name]:
            print(f'[yellow]{name} could not be found!')
            product_offers.pop(name)

    if not product_offers:
        raise ValueError('No products could be found')
    return product_offers


def display(products: List[str]):
    """ Displays various product comparisons. """
    product_offers = get_product_offers(products)
    compare_offers(product_offers)
    best_offers_by_merchant(product_offers)
    generate_offer_table(product_offers)
    send_email(product_offers,
               SECRETS['emails']['sender'],
               SECRETS['app_passwords']['google'],
               [email for email in SECRETS['emails'].values() if email != SECRETS['emails']['sender']])



def get_search_items():
    grocy_products = requests.get(f"{SECRETS['urls']['grocy']}/api/objects/products",
                                  headers={"GROCY-API-KEY":SECRETS['api_keys']['grocy']}).json()

    active_products = filter(lambda product: product['userfields']['IsActiveSearch'] == '1', grocy_products)

    products_by_search_friendly_names = []
    for product in active_products:
        search_name = product['userfields']['SearchNames']
        if ("\n" in search_name):   #FIXME: Grocy adds newline characters
            search_names = search_name.split('\n')
            [products_by_search_friendly_names.append(searchName) for searchName in search_names]
        else:
            products_by_search_friendly_names.append(search_name)

    return products_by_search_friendly_names


if __name__ == '__main__':
    display(products = get_search_items())