import logging
import random
import time
from typing import Dict, List
from uuid import UUID

import requests
from clapy import IServiceProvider
from flask import Blueprint, current_app, jsonify, request
from pydantic import BaseModel

from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from framework.merchant_api.infrastructure.merchant_data_providers import \
    get_healthy_merchant_data_providers
from framework.merchant_api.services.iconfiguration_manager import \
    IConfigurationManager
from framework.merchant_api.services.iproduct_image_provider import IProductImageProvider

PRODUCT_ROUTER = Blueprint("PRODUCT_ROUTER", __name__, url_prefix="/api/products")

# TODO: Need to more closely inspect items such as fruit and veg for pricing information,
# see IGA uses whole price, also sometimes it's an "each" pricing


@PRODUCT_ROUTER.route("/search", methods = ["POST"])
async def search_for_product_async() -> List[ScrapedProductOffer]:
    class SearchForProductQuery(BaseModel):
        merchants_to_search: List[str]
        result_limit: int = 20
        search_term: str

    _RequestBody = SearchForProductQuery.model_validate(request.get_json())

    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)
    _Logger = logging.getLogger(__name__)
    _DataProviders = get_healthy_merchant_data_providers()
    _ScrapedOffers: List[ScrapedProductOffer] = []

    _MerchantsToSearch = [
        _Merchant
        for _Merchant
        in _ConfigurationManager.get_all_merchants()
        if _Merchant.is_enabled
        and _Merchant.name.value in _RequestBody.merchants_to_search
    ]

    _Offers: List[ScrapedProductOffer] = []
    for _Merchant in _MerchantsToSearch:

        for _MerchantDataProvider in _DataProviders:

            if not _MerchantDataProvider.is_merchant_supported(_Merchant):
                continue

            try:
                if _Offers := _MerchantDataProvider.search_by_term(_RequestBody.search_term, _Merchant, _RequestBody.result_limit):
                    _ScrapedOffers.extend(_Offers)
                    break

            except Exception as e:
                _MerchantDataProvider.is_healthy = False
                _Logger.exception(f"Merchant Data Provider '{_MerchantDataProvider.base_url}' encountered a problem."
                                  f" Search term: {_RequestBody.search_term}. Merchant: {_Merchant.name.value}", e)

    _ProductImageProvider: IProductImageProvider = _ServiceProvider.get_service(IProductImageProvider)
    for _Offer in _Offers:
        _Offer.image = _ProductImageProvider.get_image(_Offer.image_uri)

    return jsonify(_ScrapedOffers)


@PRODUCT_ROUTER.route("/offers")
async def get_product_offers_async():
    _Logger = logging.getLogger(__name__)
    _DataProviders = get_healthy_merchant_data_providers()

    # TODO: Should MAPI be getting dora products and saving to them, or should the calling code of MAPI be responsible for this?
    _SavedProducts = [
        DoraProduct(**_Product)
        for _Product
        in requests.get("http://127.0.0.1:5170/api/products").json()
    ]

    # TODO: Can any of this be cached? If product offer grabbed in the last week?

    _OffersByProductID: Dict[UUID, ScrapedProductOffer] = {}

    _MerchantMapping = {
        SupportedMerchant.ALDI.value: SupportedMerchant.ALDI,
        SupportedMerchant.COLES.value: SupportedMerchant.COLES,
        SupportedMerchant.IGA.value: SupportedMerchant.IGA,
        SupportedMerchant.WOOLWORTHS.value: SupportedMerchant.WOOLWORTHS
    }

    for _Product in _SavedProducts:
        _Merchant = _MerchantMapping.get(_Product.merchant_name)
        time.sleep(random.uniform(0, 0.5))

        for _MerchantDataProvider in _DataProviders:

            if not _MerchantDataProvider.is_merchant_supported(_Merchant):
                continue

            try:
                raise Exception("aaaa")
                if _Offer := _MerchantDataProvider.get_product(_Product):
                    _OffersByProductID[_Product.product_id] = _Offer
                    break

            except Exception as e:  # TODO: Double check logger is actually logging, saw it not working
                _MerchantDataProvider.is_healthy = False
                _Logger.exception(f"Merchant Data Provider '{_MerchantDataProvider.base_url}' encountered a problem."
                                  f" Product: {_Product.name}. Merchant: {_Merchant}", e)

    for _ProductID, _Offer in _OffersByProductID.items():
        requests.patch('http://127.0.0.1:5170/api/products', {
            'is_available': _Offer.is_available,
            'price_id': _ProductID,
            'price_now': _Offer.price_now,
            'price_was': _Offer.price_was,
        })

        # Instead of regetting the image from its web source, copy it from the saved product.
        _Offer.image = next(_Product.image for _Product in _SavedProducts if _Product.product_id == _ProductID)

    return jsonify(_OffersByProductID.values())
