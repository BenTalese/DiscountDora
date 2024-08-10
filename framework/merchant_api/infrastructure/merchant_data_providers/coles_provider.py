import json
import logging
import random
import time
from typing import List

from bs4 import BeautifulSoup
from pydantic import ValidationError

from domain.entities.merchant import Merchant
from framework.merchant_api.domain.entities.coles_product_offer import \
    ColesProductOffer
from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from framework.merchant_api.infrastructure.session import get_cached_session
from framework.merchant_api.services.imerchant_data_provider import \
    IMerchantDataProvider


class ColesProvider(IMerchantDataProvider):

    #region ---------------- Fields ----------------

    _logger = logging.getLogger(__name__)

    #endregion Fields

    #region ---------------- Properties ----------------

    @property
    def base_url(self) -> str:
        return 'https://www.coles.com.au'

    @property
    def priority(self) -> int:
        return 1

    @property
    def supported_merchants(self) -> List[str]:
        return [
            SupportedMerchant.COLES
        ]

    #endregion Properties

    #region ---------------- Methods ----------------

    def get_product(self, product: DoraProduct) -> ScrapedProductOffer | None:
        with get_cached_session() as _Session:
            _Response = _Session.get(self.base_url)
            _Soup = BeautifulSoup(_Response.text, features="html.parser")
            _BuildID = json.loads(_Soup.find(id='__NEXT_DATA__').contents[0])['buildId']

            _Url = f'{self.base_url}/_next/data/{_BuildID}/en/search.json'
            _Params = {
                'q': product.name,
                'page': 1
            }

            _PageSearchResult = _Session.get(_Url, _Params).json()['pageProps']['searchResults']
            for _ProductSearchResult in _PageSearchResult['results']:
                if _ProductSearchResult['_type'] == "PRODUCT" and str(_ProductSearchResult["id"]) == product.merchant_stockcode:
                    try:
                        return self._translate_offer(ColesProductOffer.model_validate(_ProductSearchResult))

                    except ValidationError as e:
                        for _Error in e.errors():
                            self._logger.exception(
                                f"Pydantic error in {_Error['loc']}: {_Error['msg']}, received value: {_Error['input']}"
                            )

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        with get_cached_session() as _Session:
            _Response = _Session.get(self.base_url)
            _Soup = BeautifulSoup(_Response.text, features="html.parser")
            _BuildID = json.loads(_Soup.find(id='__NEXT_DATA__').contents[0])['buildId']

            _Url = f'{self.base_url}/_next/data/{_BuildID}/en/search.json'
            _Params = {
                'q': search_term,
                'page': 1
            }

            _ScrapedProductOffers: List[ScrapedProductOffer] = []
            _StartTime = time.time()

            while time.time() - _StartTime < self._max_attempt_time_seconds:
                _PageSearchResult = _Session.get(_Url, _Params).json()['pageProps']['searchResults']

                if not _PageSearchResult['results']:
                    return _ScrapedProductOffers

                for _ProductSearchResult in _PageSearchResult['results']:
                    if _ProductSearchResult['_type'] == "PRODUCT":
                        try:
                            _ScrapedProductOffers.append(
                                self._translate_offer(
                                    ColesProductOffer.model_validate(_ProductSearchResult)
                                )
                            )

                        except ValidationError as e:
                            for _Error in e.errors():
                                self._logger.exception(
                                    f"Pydantic error in {_Error['loc']}: {_Error['msg']}, received value: {_Error['input']}"
                                )

                    if len(_ScrapedProductOffers) >= result_limit:
                        return _ScrapedProductOffers

                _Params['page'] += 1
                time.sleep(random.uniform(0, self._max_backoff_time_seconds))

    def _translate_offer(self, offer: ColesProductOffer) -> ScrapedProductOffer:
        _Value, _Unit = ScrapedProductOffer._extract_value_and_unit_from_size(offer.size)

        return ScrapedProductOffer(
            brand = offer.brand,
            image = None,
            image_uri = f"https://productimages.coles.com.au/productimages{offer.imageUris[0].uri}",
            is_available = offer.availability,
            merchant_name = SupportedMerchant.COLES.value,
            merchant_stockcode = str(offer.id),
            name = offer.name if offer.brand in offer.name else f"{offer.brand} {offer.name}",
            price_now = offer.pricing.now if offer.pricing else 0,
            price_per_cup = offer.pricing.comparable.upper() if offer.pricing else None,
            price_was = offer.pricing.was if offer.pricing else 0,
            size = offer.size.upper(),
            size_unit = _Unit or offer.size.upper(),
            size_value = _Value,
            web_url = f"{self.base_url}/product/{offer.id}"
        )

    #endregion Methods
