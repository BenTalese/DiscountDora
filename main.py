from typing import List, Any, Dict, Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib, ssl
import requests
import json
from rich import print

from examples import compare_offers, best_offers_by_merchant, generate_offer_table
from emailing.generate import generate_weekly_email
from search import coles, woolies
from search.types import ProductOffers

secrets = json.load(open('secrets.json'))

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
    send_price_report_email(products)


def send_price_report_email(products: List[str]):
    product_offers = get_product_offers(products)

    text = "Oopsie, something went wrongsie :("
    html = generate_weekly_email(product_offers)

    message = MIMEMultipart('alternative')
    message.attach(MIMEText(text, 'plain'))
    message.attach(MIMEText(html, 'html'))

    # Generate & send email
    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = secrets['emails']['sender']
    receiver1_email = secrets['emails']['ben']
    receiver2_email = secrets['emails']['xi']
    app_password = secrets['app_passwords']['google']

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver1_email, message.as_string())
        #server.sendmail(sender_email, receiver2_email, message.as_string())


def get_search_items():
    grocy_products = requests.get(f"{secrets['urls']['grocy']}/api/objects/products",
                                  headers={"GROCY-API-KEY":secrets['api_keys']['grocy']}).json()

    active_products = filter(lambda product: product['userfields']['IsActiveSearch'] == '1', grocy_products)

    products_by_search_friendly_names = []
    for product in active_products:
        search_name = product['userfields']['SearchNames']
        if ("\n" in search_name):   # Grocy adds newline characters
            search_names = search_name.split('\n')
            [products_by_search_friendly_names.append(searchName) for searchName in search_names]
        else:
            products_by_search_friendly_names.append(search_name)

    return products_by_search_friendly_names


if __name__ == '__main__':
    display(products = get_search_items())