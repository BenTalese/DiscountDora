import os
import sys
from urllib.parse import urljoin

import requests

sys.path.append(os.getcwd())

import json
from typing import Generator, List, Optional

from bs4 import BeautifulSoup
from pydantic import BaseModel, Extra
from typing_extensions import Literal

from framework.merchant_api.infrastructure.session import create_session

_session = create_session()


def _init() -> str:
    url = 'https://www.coles.com.au/'
    response = _session.get(url=url)
    soup = BeautifulSoup(response.text, features="html.parser")
    api_data = json.loads(soup.find(id='__NEXT_DATA__').contents[0])
    build_id = api_data['buildId']  # 20221208.01_v3.19.0
    return build_id


_BUILD_ID = _init()

# NOTE: This is product domain
class Product(BaseModel, extra=Extra.allow):
    merchant: str = 'coles'

    # NOTE: Looks like sub classes, should be domain entities also??
    class Pricing(BaseModel, extra=Extra.allow):
        class Unit(BaseModel, extra=Extra.allow):
            quantity: int = 0 # 1
            #ofMeasureQuantity: Optional[int]  # 100
            #ofMeasureUnits: Optional[str]  # "g"
            #price: Optional[float]  # 2
            #ofMeasureType: Optional[str]  # "g"
            #isWeighted: bool = False  # false

        now: float = 0 # 6
        was: float = 0 # 6.5
        saveAmount: Optional[float] = 0  # 0.5
        #priceDescription: Optional[str]  # "Was $6.50 on Sep 2022"
        #savePercent: Optional[float]  # 50
        saveStatement: Optional[str] = ""  # "save $5.00"
        #unit: Unit

        #comparable: str  # "$2.00 per 100g"
        #promotionType: Optional[str]  # "DOWNDOWN", "SPECIAL"
        #specialType: Optional[str]  # "PERCENT_OFF", "MULTI_SAVE", "WHILE_STOCKS_LAST"
        #onlineSpecial: bool  # false

    #_type: Literal['PRODUCT']     # TODO: WTF IS THIS?
    id: int = 0 # 2351888
    name: str = "" # "Cadbury Clinkers Lollies"
    brand: str = "" # "Pascall"
    #description: str  # "PASCALL CADBURY CLINKERS 300G"
    size: str = "" # "300g"
    availability: bool = False # true
    #availabilityType: str  # "InStoreAndOnline"
    pricing: Optional[Pricing] = None # None if `availability=False`

    def __str__(self):
        price_str = f"unavailable ${self.pricing}"
        if self.availability:
            price_str = f'${self.pricing.now}'
            if self.pricing.saveStatement:
                price_str += f' ({self.pricing.saveStatement})'
        return f"{self.brand} {self.name} {self.size} | {price_str}"

    @property
    def display_name(self) -> str:
        return f""

    @property
    def price(self) -> Optional[float]:
        return self.pricing.now if self.availability else None

    @property
    def is_on_special(self) -> Optional[bool]:
        return self.pricing.saveAmount is not None if self.pricing is not None else False #FIXME: Put this if here just to stop it crashing when pricing is None

    @property
    def link(self) -> str:
        return f'https://www.coles.com.au/product/{self.id}' # NOTE: Doesn't seem like it's necessary to have the display name, only ID required for URL to resolve


# NOTE: Looks like webscraper-specific domain
class ProductPageSearchResult(BaseModel, extra=Extra.allow):
    start: int = 0 # 0
    didYouMean: Optional[list] # null
    noOfResults: int = 0 # 182
    start: int = 0 # 0
    pageSize: int = 0 # 48
    keyword: str = "" # "cadbury chocolate"
    resultType: int = 0 # 1
    results: List[Product]

    def search_exact(self, product_name: str) -> Optional[Product]:
        """ Return product that matches product_name within list of paged results """
        for product in self.results:
            if product.name == product_name:
                return product
        else:
            return None


def im_feeling_lucky(search_term: str) -> Generator[Product, None, None]:
    paginated_search = search(search_term)
    for page in paginated_search:
        for product in page.results:
            yield product


def search(search_term: str, specials_only: bool = False) -> Generator[ProductPageSearchResult, None, None]:
    url = f'https://www.coles.com.au/_next/data/{_BUILD_ID}/en/search.json'
    params = {
        'q': search_term,
        'page': 1,
    }
    if specials_only:
        params['filter_Special'] = 'all'

    _SuggestedTerm: str = None
    while True:
        response = _session.get(url=url, params=params).json()
        # # TODO: for each coles product, set the image uri
        # xyz = requests.get('https://www.coles.com.au/product/8836879')
        # img_tags = BeautifulSoup(xyz.text, 'html.parser').find_all('img')
        # img_urls = [urljoin(url, img['src']) for img in img_tags]

        _SuggestedTerm = response['pageProps']['searchResults']['didYouMean'] # TOOD: Return out of use case as separate parameter
        search_page = ProductPageSearchResult.model_validate(response['pageProps']['searchResults'])
        if search_page.noOfResults == 0:
            break
        yield search_page
        params['page'] += 1


if __name__ == '__main__':
    gen = search('soda')
    print(next(gen))
