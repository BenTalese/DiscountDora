import logging
import random
import time
from base64 import b64encode
from itertools import groupby
from typing import Dict, List
from uuid import UUID

import requests
from clapy import IServiceProvider
from flask import Blueprint, current_app, jsonify

from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from framework.merchant_api.infrastructure.merchant_data_providers.coles_provider import \
    ColesProvider
from framework.merchant_api.infrastructure.merchant_data_providers.grocerize_provider import \
    GrocerizeProvider
from framework.merchant_api.infrastructure.merchant_data_providers.iga_provider import \
    IGAProvider
from framework.merchant_api.infrastructure.merchant_data_providers.save_on_groceries_provider import \
    SaveOnGroceriesProvider
from framework.merchant_api.infrastructure.merchant_data_providers.woolworths_provider import \
    WoolworthsProvider
from framework.merchant_api.infrastructure.session import get_cached_session
from framework.merchant_api.services.iconfiguration_manager import \
    IConfigurationManager
from framework.merchant_api.services.imerchant_data_provider import \
    IMerchantDataProvider

PRODUCT_ROUTER = Blueprint("PRODUCT_ROUTER", __name__, url_prefix="/api/products")

'''
REQUIREMENTS:
    - Can check which sources are healthy/working in the UI
    - Can turn sources on/off
    - Periodically check health of sources (also on startup) and skip unhealthy sources when scraping

On navigation to product search, if nothing is configured open a modal to configure settings, or
    give them a link to the config page (config is part of product search page not its own page maybe?)
    - If all merchants are disabled -> send user to choose their merchants
    - This requires us to change the merchant endpoint to grab the enabled merchants, not the supported merchants
        - May want to have 2 endpoints, one for each option

SEPARATE SETTINGS PAGE (Atif idea)
'''
# TODO: Need to more closely inspect items such as fruit and veg for pricing information, see IGA uses whole price, also sometimes it's an "each" pricing


@PRODUCT_ROUTER.route("/search/<search_term>")
@PRODUCT_ROUTER.route("/search/<search_term>/<result_limit>")
async def search_for_product_async(search_term: str, result_limit: int = 10) -> List[ScrapedProductOffer]:
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)
    _Logger: logging.Logger = _ServiceProvider.get_service(logging.Logger)

    _ScrapedOffers: List[ScrapedProductOffer] = []

    # TODO: Move to method "get_healthy_providers"
    _DataProviders: List[IMerchantDataProvider] = [
        _ServiceProvider.get_service(ColesProvider),
        _ServiceProvider.get_service(IGAProvider),
        _ServiceProvider.get_service(GrocerizeProvider),
        _ServiceProvider.get_service(SaveOnGroceriesProvider),
        _ServiceProvider.get_service(WoolworthsProvider)
    ]

    _HealthyDataProviders = [_Provider for _Provider in _DataProviders if _Provider.is_healthy]
    _HealthyDataProviders.sort(key = lambda mdp: mdp.priority)

    for _Merchant in _ConfigurationManager.get_enabled_merchants():
        for _MerchantDataProvider in _HealthyDataProviders:

            if not _MerchantDataProvider.is_merchant_supported(_Merchant):
                continue

            time.sleep(random.uniform(0, 2))
            try:
                if _Offers := _MerchantDataProvider.search_by_term(search_term, _Merchant, result_limit):
                    _ScrapedOffers.extend(_Offers)
                    break

            except Exception as e:
                _MerchantDataProvider.is_healthy = False
                _Logger.exception(f"Merchant Data Provider '{_MerchantDataProvider.base_url}' encountered a problem."
                                  f" Search term: {search_term}. Merchant: {_Merchant.name.value}", e)

    with get_cached_session() as _Session:
        for _Offer in _ScrapedOffers:
            _Offer.image = b64encode(_Session.get(_Offer.image_uri).content).decode('utf-8')

    return jsonify(_ScrapedOffers)


@PRODUCT_ROUTER.route("/offers")
async def get_product_offers_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _Logger: logging.Logger = _ServiceProvider.get_service(logging.Logger)

    # TODO: Should MAPI be getting dora products and saving to them, or should the calling code of MAPI be responsible for this?
    _SavedProducts = sorted(
        (DoraProduct(**_Product) for _Product in requests.get("http://127.0.0.1:5170/api/products").json()),
        key = lambda dp: dp.merchant_name
    )

    _SavedProductsByMerchant = {key: list(group) for key, group in groupby(_SavedProducts, key = lambda sp: sp.merchant_name)}

    _OffersByProductID: Dict[UUID, ScrapedProductOffer] = {}

    _DataProviders: List[IMerchantDataProvider] = [
        _ServiceProvider.get_service(ColesProvider),
        _ServiceProvider.get_service(IGAProvider),
        _ServiceProvider.get_service(GrocerizeProvider),
        _ServiceProvider.get_service(SaveOnGroceriesProvider),
        _ServiceProvider.get_service(WoolworthsProvider)
    ]

    _HealthyDataProviders = sorted(
        (_Provider for _Provider in _DataProviders if _Provider.is_healthy),
        key = lambda mdp: mdp.priority
    )

    for _Merchant, _Products in _SavedProductsByMerchant.items():  # TODO: Seems redundant, but product does not have a "Merchant", only by name
        for _Product in _Products:

            for _MerchantDataProvider in _HealthyDataProviders:

                if not _MerchantDataProvider.is_merchant_supported(_Merchant):
                    continue

                time.sleep(random.uniform(0, 0.3))
                try:
                    if _Offer := _MerchantDataProvider.get_product(_Product):
                        _OffersByProductID[_Product.product_id] = _Offer
                        break

                except Exception as e:
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
