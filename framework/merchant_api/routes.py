from base64 import b64encode
import json
import os
from typing import Dict, List
from uuid import UUID

import requests
from flask import Blueprint, jsonify

from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from framework.merchant_api.infrastructure.session import create_session
from framework.merchant_api.scrapers import coles_scraper, iga_scraper, woolworths_scraper

# TODO: Logging --- would be useful to know what the search term was that caused the error, and which merchant, etc
# TODO: Need to more closely inspect items such as fruit and veg for pricing information, see IGA uses whole price, also sometimes it's an "each" pricing
# FIXME: If anything goes wrong you just get a 500 response, no logging and no response body to tell you the problem
# FIXME: These routers are looking a bit ugly, there's always a cleaner, better way to do things

PRODUCT_ROUTER = Blueprint("PRODUCT_ROUTER", __name__, url_prefix="/api/products")


@PRODUCT_ROUTER.route("/search/<search_term>")
@PRODUCT_ROUTER.route("/search/<search_term>/<start_page>")
@PRODUCT_ROUTER.route("/search/<search_term>/<start_page>/<result_limit>")
async def search_for_product_async(search_term: str, start_page: int = 1, result_limit: int = 10) -> List[ScrapedProductOffer]:
    with create_session() as _Session:
        _Session.get('https://www.woolworths.com.au')
        _WoolworthsProductOffers = [
            ScrapedProductOffer.translate_woolworths_offer(_ProductOffer)
            for _ProductOffer
            in woolworths_scraper.search(_Session, search_term, start_page, start_page + 1, result_limit)
        ]

        # FIXME: Repeating code
        _IgaStoreID: int
        _BaseDir = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(_BaseDir,'appsettings.json'), 'r') as _Configuration:
            _IgaStoreID = json.load(_Configuration)['IGA_STORE_ID']

        _Session.get('https://www.igashop.com.au/')
        _IgaProductOffers = [
            ScrapedProductOffer.translate_iga_offer(_ProductOffer)
            for _ProductOffer
            in iga_scraper.search(_Session, _IgaStoreID, search_term, start_page, start_page + 1, result_limit)
        ]

        _Session.get('https://www.coles.com.au/')
        _ColesProductOffers = [
            ScrapedProductOffer.translate_coles_offer(_ProductOffer)
            for _ProductOffer
            in coles_scraper.search(_Session, search_term, start_page, start_page + 1, result_limit)
        ]

        _ScrapedOffers = _WoolworthsProductOffers + _IgaProductOffers + _ColesProductOffers
        for _Offer in _ScrapedOffers:
            _Offer.image = b64encode(_Session.get(_Offer.image_uri).content).decode('utf-8')

        return jsonify(_ScrapedOffers)


@PRODUCT_ROUTER.route("/offers")
async def get_product_offers_async():
    _SavedProducts = [
        DoraProduct(**_Product)
        for _Product
        in requests.get("http://127.0.0.1:5170/api/products").json()
    ]

    _OffersByProductID: Dict[UUID, ScrapedProductOffer] = {}
    with create_session() as _Session:
        _Session.get('https://www.woolworths.com.au/')
        for _Product in _SavedProducts:
            if _Product.merchant_name == SupportedMerchant.WOOLWORTHS:
                _OffersByProductID[_Product.product_id] = ScrapedProductOffer.translate_woolworths_offer(
                    woolworths_scraper.get_by_stockcode(_Session, _Product.merchant_stockcode)
                )

        _IgaStoreID: int
        _BaseDir = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(_BaseDir,'appsettings.json'), 'r') as _Configuration:
            _IgaStoreID = json.load(_Configuration)['IGA_STORE_ID']

        _Session.get('https://www.igashop.com.au/')
        for _Product in _SavedProducts:
            if _Product.merchant_name == SupportedMerchant.IGA:
                _OffersByProductID[_Product.product_id] = ScrapedProductOffer.translate_iga_offer(
                    iga_scraper.get_by_stockcode(_Session, _IgaStoreID, _Product.merchant_stockcode)
                )

        _ResponseText = _Session.get('https://www.coles.com.au/').text
        for _Product in _SavedProducts:
            if _Product.merchant_name == SupportedMerchant.COLES:
                _OffersByProductID[_Product.product_id] = ScrapedProductOffer.translate_coles_offer(
                    coles_scraper.get_by_stockcode(_Session, _ResponseText, _Product.merchant_stockcode, _Product.name)
                )

    for _ProductID, _Offer in _OffersByProductID.items():
        requests.patch('http://127.0.0.1:5170/api/products', {
            'is_available': _Offer.is_available,
            'price_id': _ProductID,
            'price_now': _Offer.price_now,
            'price_was': _Offer.price_was,
        })

        _Offer.image = next(_Product.image for _Product in _SavedProducts if _Product.product_id == _ProductID)

    return jsonify(_OffersByProductID.values())
