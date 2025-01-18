""" A collection of display examples for product comparisons """

from collections import defaultdict
from typing import Dict, List
from typing_extensions import Literal

from rich import box
from rich.console import Console
from rich.table import Table

from framework.merchant_api.types import ProductOffers, Merchant, Product

_console = Console()


# from _misc.examples import compare_offers, best_offers_by_merchant, generate_offer_table
# from framework.web_scraper import coles_old, woolies_old
# from framework.web_scraper.types import ProductOffers
# from framework.emailer.delivery import send_email

# # current_dir = os.path.dirname(os.path.abspath(__file__))
# # with open(os.path.join(current_dir, 'secrets.json'), 'r') as file:
# #     SECRETS = json.load(file)

# #TODO: Currently unavailable products come up as not found

# def get_product_offers(product_names: List[str]) -> ProductOffers:
#     """ Returns ProductOffers object with optimistic search results for product_names. """
#     product_offers: Dict[str, List[Any]] = {}
#     for name in product_names:
#         product_offers[name] = []
#         for merchant in [coles_old, woolies_old]:
#             merchant_product_search = merchant.im_feeling_lucky(name)

#             product = next(merchant_product_search, None)
#             if (product is not None):
#                 product_offers[name].append(product)

#         if not product_offers[name]:
#             print(f'[yellow]{name} could not be found!')
#             product_offers.pop(name)

#     if not product_offers:
#         raise ValueError('No products could be found')
#     return product_offers


# def display(products: List[str]):
#     """ Displays various product comparisons. """
#     product_offers = get_product_offers(products)
#     compare_offers(product_offers)
#     best_offers_by_merchant(product_offers)
#     generate_offer_table(product_offers)
#     # send_email(product_offers,
#     #            SECRETS['emails']['sender'],
#     #            SECRETS['app_passwords']['google'],
#     #            [email for email in SECRETS['emails'].values() if email != SECRETS['emails']['sender']])



# def get_search_items():
#     return ["Chocolate"]

    # grocy_products = requests.get(f"{SECRETS['urls']['grocy']}/api/objects/products",
    #                               headers={"GROCY-API-KEY":SECRETS['api_keys']['grocy']}).json()

    # active_products = filter(lambda product: product['userfields']['IsActiveSearch'] == '1', grocy_products)

    # products_by_search_friendly_names = []
    # for product in active_products:
    #     search_name = product['userfields']['SearchNames']
    #     if ("\n" in search_name):   #FIXME: Grocy adds newline characters
    #         search_names = search_name.split('\n')
    #         [products_by_search_friendly_names.append(searchName) for searchName in search_names]
    #     else:
    #         products_by_search_friendly_names.append(search_name)

    # return products_by_search_friendly_names


def compare_offers(product_offers: ProductOffers):
    # Compare all offers by product
    for name, products in product_offers.items():
        _console.print('\n' + name, style='underline')

        lowest_price = min(products).price
        cheapest_product_idx = [i for i in range(len(products)) if products[i].price == lowest_price]
        is_sales = any((_product.is_on_special for _product in products))
        for i, _product in enumerate(products):
            txt_colour = 'green' if is_sales and i in cheapest_product_idx else 'grey50'
            # txt_colour = None if not i else 'grey50'
            _console.print(f'  {_product.merchant.upper()}: {_product}', style=txt_colour)
    _console.print('\n')


def best_offers_by_merchant(product_offers: ProductOffers):
    # Collect the cheapest offer
    cheapest_products_by_merchant: Dict[Merchant | Literal['either'], List[Product]] = defaultdict(list)
    for products in product_offers.values():
        is_all_same_price = len(set(p.price for p in products)) == 1
        if is_all_same_price:
            cheapest_products_by_merchant['either'].append(products[0])
        else:
            cheapest_product = min(products)
            _merchant: Merchant = cheapest_product.merchant
            cheapest_products_by_merchant[_merchant].append(cheapest_product)

    _console.print("[bold yellow]shopping list")
    _console.print(
        {merchant: [str(p) for p in products] for merchant, products in cheapest_products_by_merchant.items()}
    )


def generate_offer_table(product_offers: ProductOffers, verbose: bool = True) -> Table:
    table = Table(show_header=True, header_style="bold yellow", box=box.SIMPLE_HEAD)
    table.add_column("shopping list", max_width=78)
    for merchant in ["coles", "woolies"]:
        table.add_column(merchant, justify="right", max_width=8)

    for product_name, products in product_offers.items():
        lowest_price = min(products).price
        cheapest_product_idx = [i for i in range(len(products)) if products[i].price == lowest_price]
        is_sales = any((_product.is_on_special for _product in products))
        row = [product_name]
        for i, _product in enumerate(products):
            txt_colour = '[green]' if is_sales and i in cheapest_product_idx else '[grey85]'
            price = f'${_product.price}' if _product.price is not None else 'n/a'
            row.append(txt_colour + price)
        table.add_row(*row)

    if verbose:
        _console.print(table)

    return table
