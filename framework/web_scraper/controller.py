import base64
import os
import sys
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image
from framework.web_scraper.get_products_presenter import GetProductsPresenter
from framework.web_scraper.get_merchants_presenter import GetMerchantsPresenter
from interface_adaptors.controllers.merchant_controller import MerchantController

from interface_adaptors.controllers.product_controller import ProductController

sys.path.append(os.getcwd())

from typing import List

from framework.web_scraper import coles_logic, woolworths_logic
from framework.web_scraper.models import ScrapedProductOffer
from framework.web_scraper.session import create_session

# TODO: Make into use cases, this'll do for now though
# TODO: Logging --- would be useful to know what the search term was that caused the error, and which merchant, etc
# TODO: This is probably an action (combining use cases)

# class WebScraper:
#     def __init__(self, merchant_controller: MerchantController, product_controller: ProductController):
#         self.merchant_controller = merchant_controller
#         self.product_controller = product_controller

def search_for_product(self, search_term: str, start_page: int = 1, limit_results_to: int = 10) -> List[ScrapedProductOffer]:
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

    # def scrape_product_offers(self) -> List[ScrapedProductOffer]:
    #     # TODO: Either own service collection, or this is part of the API...
    #     #       -> I think make this a hosted service, kept here in this folder, with the product controller as a dependency

    #     _GetMerchantsPresenter = GetMerchantsPresenter()
    #     self.merchant_controller.get_merchants_async(_GetMerchantsPresenter)

    #     _GetProductsPresenter = GetProductsPresenter()
    #     self.product_controller.get_products_async(_GetProductsPresenter)

    #     with create_session() as _Session:
    #         _WoolworthsMerchantID = next(_Merchant.merchant_id for _Merchant in _GetMerchantsPresenter.merchants if _Merchant.name == "Woolworths")
    #         _WoolworthsProductOffers = [
    #             ScrapedProductOffer.translate_woolworths_offer(woolworths_logic.get_by_stockcode(_Session, _Product.merchant_stockcode))
    #             for _Product
    #             in _GetProductsPresenter.products
    #             if _Product.merchant_id == _WoolworthsMerchantID
    #         ]

    #         _ColesMerchantID = next(_Merchant.merchant_id for _Merchant in _GetMerchantsPresenter.merchants if _Merchant.name == "Coles")
    #         _ColesProductOffers = [
    #             ScrapedProductOffer.translate_coles_offer(coles_logic.get_by_stockcode(_Session, _Product.merchant_stockcode))
    #             for _Product
    #             in _GetProductsPresenter.products
    #             if _Product.merchant_id == _ColesMerchantID
    #         ]

    #         # save new deals (new use case, either UpdateProduct or CreateProductOffer)
    #         # return new deals?



# if __name__ == "__main__":
#     x = search_for_product("water")
#     # x.sort(key=lambda x: x.price_now)
#     g = Image.open(BytesIO(requests.get(x[0].image).content))
#     h = requests.get(x[0].image).content
#     print(type(h))
#     v = 0
