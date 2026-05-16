import logging

from flask import jsonify, request
from pydantic import BaseModel

from merchant_api.domain.entities.scraped_product_offer import ScrapedProductOffer
from merchant_api.infrastructure.configuration_manager import CONFIGURATION_MANAGER
from merchant_api.infrastructure.merchant_data_providers import get_healthy_providers
from merchant_api.infrastructure.product_image_provider import PRODUCT_IMAGE_PROVIDER
from merchant_api.infrastructure.similarity import get_similarity_score
from merchant_api.routers import PRODUCT_ROUTER


@PRODUCT_ROUTER.route("/search", methods = ["POST"])
def search_for_product():
    class SearchForProductQuery(BaseModel):
        merchants_to_search: list[str]
        result_limit: int
        search_term: str

    _Logger = logging.getLogger(__name__)
    _Logger.info("Search for product requested.")

    _RequestBody = SearchForProductQuery.model_validate(request.get_json())
    _Logger.info(f"Searching with term: '{_RequestBody.search_term}'")

    _DataProviders = get_healthy_providers()
    _ScrapedOffers: list[ScrapedProductOffer] = []

    _MerchantsToSearch = [
        _Merchant
        for _Merchant
        in CONFIGURATION_MANAGER.get_all_merchants()
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

    for _Offer in _ScrapedOffers:
        _Offer.image = PRODUCT_IMAGE_PROVIDER.get_image(_Offer.image_uri)

    return jsonify(_ScrapedOffers)
