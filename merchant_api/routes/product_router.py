import logging
import random
import time
from typing import Dict, List
from uuid import UUID

import requests
from clapy import IServiceProvider
from flask import Blueprint, current_app, jsonify, request
from pydantic import BaseModel

from merchant_api.domain.entities.dora_product import DoraProduct
from merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from merchant_api.infrastructure.merchant_data_providers import \
    get_healthy_merchant_data_providers
from merchant_api.infrastructure.similarity import get_similarity_score
from merchant_api.services.iconfiguration_manager import IConfigurationManager
from merchant_api.services.iproduct_image_provider import IProductImageProvider

PRODUCT_ROUTER = Blueprint("PRODUCT_ROUTER", __name__, url_prefix="/api/products")


@PRODUCT_ROUTER.route("/search", methods = ["POST"])
async def search_for_product_async() -> List[ScrapedProductOffer]:
    class SearchForProductQuery(BaseModel):
        merchants_to_search: List[str]
        result_limit: int
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

    for _Merchant in _MerchantsToSearch:

        for _MerchantDataProvider in _DataProviders:

            if not _MerchantDataProvider.is_merchant_supported(_Merchant):
                continue

            try:
                if _Offers := _MerchantDataProvider.search_by_term(_RequestBody.search_term, _Merchant, _RequestBody.result_limit):

                    _ScrapedOffers.extend([
                        _Offer
                        for _Offer
                        in _Offers
                        if not any(
                            _Offer.name.lower().strip() == _ExistingOffer.name.lower().strip()
                            and _Offer.merchant_name == _ExistingOffer.merchant_name
                            for _ExistingOffer
                            in _ScrapedOffers)
                    ])

                    break

            except Exception:
                _MerchantDataProvider.is_healthy = False
                _Logger.exception(f"Merchant data provider '{_MerchantDataProvider.base_url}' encountered a problem,"
                                  f" search term: '{_RequestBody.search_term}', merchant: '{_Merchant.name.value}'.")

    _ScrapedOffers = sorted(
        _ScrapedOffers,
        key=lambda _Offer: get_similarity_score(_Offer.name, _RequestBody.search_term, 70),
        reverse=True
    )

    _ProductImageProvider: IProductImageProvider = _ServiceProvider.get_service(IProductImageProvider)
    for _Offer in _ScrapedOffers:
        _Offer.image = _ProductImageProvider.get_image(_Offer.image_uri)

    return jsonify(_ScrapedOffers)


@PRODUCT_ROUTER.route("/offers")
async def get_product_offers_async():
    _Logger = logging.getLogger(__name__)
    _DataProviders = get_healthy_merchant_data_providers()

    _SavedProducts = [
        DoraProduct(**_Product)
        for _Product
        in requests.get("http://127.0.0.1:5170/api/products").json()
    ]

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
                if _Offer := _MerchantDataProvider.get_product(_Product):
                    _OffersByProductID[_Product.product_id] = _Offer
                    break

            except Exception:
                _MerchantDataProvider.is_healthy = False
                _Logger.exception(f"Merchant Data Provider '{_MerchantDataProvider.base_url}' encountered a problem."
                                  f" Product: {_Product.name}. Merchant: {_Merchant}")

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
