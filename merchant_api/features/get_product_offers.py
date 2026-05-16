import logging
import random
import time
from uuid import UUID

import requests
from flask import jsonify

from merchant_api.domain.entities.dora_product import DoraProduct
from merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from merchant_api.infrastructure.configuration_manager import CONFIGURATION_MANAGER
from merchant_api.infrastructure.merchant_data_providers import \
    get_healthy_providers
from merchant_api.routers import PRODUCT_ROUTER


@PRODUCT_ROUTER.route("/offers")
def get_product_offers():
    _Logger = logging.getLogger(__name__)
    _Logger.info("Getting updated product offers for saved products.")
    _DataProviders = get_healthy_providers()

    _SavedProducts = [
        DoraProduct(**_Product)
        for _Product
        in requests.get("http://127.0.0.1:5170/api/products").json()
    ]

    _OffersByProductID: dict[UUID, ScrapedProductOffer] = {}

    _Merchants = CONFIGURATION_MANAGER.get_all_merchants()

    for _Product in _SavedProducts:
        _Merchant = next((m for m in _Merchants if m.name == _Product.merchant_name), None)
        if not _Merchant:
            _Logger.warning(f"Product '{_Product.name}' has unsupported merchant '{_Product.merchant_name}'. Skipping.")
            continue

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
