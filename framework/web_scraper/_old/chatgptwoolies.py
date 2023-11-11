import requests
from dataclasses import dataclass
from typing import Optional

from framework.web_scraper.session import create_session

@dataclass
class Product:
    merchant: str = 'woolies'
    stockcode: int = None
    price: Optional[float] = None
    display_name: str = None
    is_on_special: bool = False

    def __str__(self):
        price_str = f"unavailable"
        if self.price is not None:
            price_str = f'${self.price}'
            if self.is_on_special:
                price_str += f' (save ${self.was_price - self.price})'
        return f"{self.display_name} | {price_str}"

def fetch_product(product_id: str) -> Product:
    url = f'https://www.woolworths.com.au/api/v3/ui/schemaorg/product/{product_id}'
    response = requests.get(url)
    data = response.json()
    return Product(
        stockcode=data['Stockcode'],
        price=data['Price'] if data['IsAvailable'] else None,
        display_name=data['DisplayName'],
        is_on_special=data['IsOnSpecial'],
        was_price=data['WasPrice']
    )

def search(search_term: str, page=1):
    session = create_session()
    session.get(url='https://www.woolworths.com.au')
    url = 'https://www.woolworths.com.au/shop/search/products'
    params = {
        'pageNumber': page,
        'pageSize': 36,
        'q': search_term
    }

    response = requests.get(url, params=params)
    data = response.json()

    for product_data in data.get('Products', []):
        yield Product(
            stockcode=product_data['Stockcode'],
            price=product_data['Price'] if product_data['IsAvailable'] else None,
            display_name=product_data['DisplayName'],
            is_on_special=product_data['IsOnSpecial'],
            was_price=product_data['WasPrice']
        )

if __name__ == '__main__':
    search_term = 'Cadbury Dairy Milk Chocolate Block 180g'
    for page_num, product_page in enumerate(search(search_term), start=1):
        print(f"Page {page_num} Results:")
        for product in product_page:
            print(product)
