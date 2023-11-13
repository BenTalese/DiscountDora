import base64
import os
import sys
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image

sys.path.append(os.getcwd())

from typing import List

from framework.web_scraper import coles_logic, woolworths_logic
from framework.web_scraper.models import ScrapedProductOffer
from framework.web_scraper.session import create_session

# TODO: Make into use cases, this'll do for now though

# This is probably an action (combining use cases)
def search_for_product(search_term: str, start_page: int = 1, limit_results_to: int = 10) -> List[ScrapedProductOffer]:
    with create_session() as _Session:
        _Session.get('https://www.woolworths.com.au') # TODO: Why do .get() here?
        _WoolworthsProductOffers = [ScrapedProductOffer.translate_woolworths_offer(_ProductOffer)
                                    for _ProductOffer
                                    in woolworths_logic.search(_Session, search_term, start_page, start_page + 1, limit_results_to)]

        _Session.get('https://www.coles.com.au/')
        _ColesProductOffers = [ScrapedProductOffer.translate_coles_offer(_ProductOffer)
                            for _ProductOffer
                            in coles_logic.search(_Session, search_term, start_page, start_page + 1, limit_results_to)]

        _ScrapedOffers = _WoolworthsProductOffers + _ColesProductOffers
        for _Offer in _ScrapedOffers:
            _Offer.image = base64.b64encode(_Session.get(_Offer.image_uri).content)

        return _ScrapedOffers


if __name__ == "__main__":
    x = search_for_product("water")
    # x.sort(key=lambda x: x.price_now)
    g = Image.open(BytesIO(requests.get(x[0].image).content))
    h = requests.get(x[0].image).content
    print(type(h))
    v = 0
