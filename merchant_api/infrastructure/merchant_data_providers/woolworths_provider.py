import logging
import random
import time
import urllib.parse

from pydantic import ValidationError

from merchant_api.domain.entities.dora_product import DoraProduct
from merchant_api.domain.entities.merchant import Merchant
from merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from merchant_api.domain.entities.woolworths_product_offer import \
    WoolworthsProductOffer
from merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from merchant_api.infrastructure.session import get_cached_session
from merchant_api.infrastructure.merchant_data_providers.merchant_data_provider import MerchantDataProvider


class WoolworthsProvider(MerchantDataProvider):

    #region ---------------- Fields ----------------

    _logger = logging.getLogger(__name__)

    #endregion Fields

    #region ---------------- Properties ----------------

    @property
    def base_url(self) -> str:
        return 'https://www.woolworths.com.au'

    @property
    def priority(self) -> int:
        return 1

    @property
    def supported_merchants(self) -> list[SupportedMerchant]:
        return [
            SupportedMerchant.WOOLWORTHS
        ]

    #endregion Properties

    #region ---------------- Methods ----------------

    def get_product(self, product: DoraProduct) -> ScrapedProductOffer | None:
        with get_cached_session() as _Session:
            _Url = f'{self.base_url}/apis/ui/Search/products'
            _Body = {
                'Location': f'/shop/search/products?{urllib.parse.urlencode({"searchTerm": product.merchant_stockcode})}',
                'PageNumber': 1,
                'PageSize': 36,
                'SearchTerm': product.merchant_stockcode,
                'SortType': "TraderRelevance"
            }

            _PageSearchResult = _Session.post(_Url, json=_Body).json()

            if not _PageSearchResult['Products']:
                return None

            try:
                return self._translate_offer(
                    WoolworthsProductOffer.model_construct(**_PageSearchResult['Products'][0]['Products'][0])
                )

            except ValidationError as e:
                for _Error in e.errors():
                    self._logger.exception(
                        f"Pydantic error in {_Error['loc']}: {_Error['msg']}, received value: {_Error['input']}"
                    )

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> list[ScrapedProductOffer]:
        with get_cached_session() as _Session:
            _Session.get(self.base_url)
            _Url = f'{self.base_url}/apis/ui/Search/products'
            _Body = {
                'Filters': [],
                'IsSpecial': False,
                'Location': f'/shop/search/products?{urllib.parse.urlencode({"searchTerm": search_term})}',
                'PageNumber': 1,
                'PageSize': 36,
                'SearchTerm': search_term,
                'SortType': "TraderRelevance"
            }

            _ScrapedProductOffers: list[ScrapedProductOffer] = []
            _StartTime = time.time()

            while time.time() - _StartTime < self._max_attempt_time_seconds:
                _PageSearchResult = _Session.post(_Url, json=_Body).json()

                if not _PageSearchResult['Products']:
                    return _ScrapedProductOffers

                for _ProductSearchResult in _PageSearchResult['Products']:
                    try:
                        _ScrapedProductOffers.append(
                            self._translate_offer(
                                WoolworthsProductOffer.model_construct(**_ProductSearchResult['Products'][0])
                            )
                        )

                    except ValidationError as e:
                        for _Error in e.errors():
                            self._logger.exception(
                                f"Pydantic error in {_Error['loc']}: {_Error['msg']}, received value: {_Error['input']}"
                            )

                    if len(_ScrapedProductOffers) >= result_limit:
                        return _ScrapedProductOffers

                _Body['PageNumber'] += 1
                time.sleep(random.uniform(0, self._max_backoff_time_seconds))

            self._logger.info(f"Merchant data provider '{self.base_url}' timed out searching for '{search_term}'.")
            return _ScrapedProductOffers

    def _translate_offer(self, offer: WoolworthsProductOffer) -> ScrapedProductOffer:
        _Value, _Unit = ScrapedProductOffer._extract_value_and_unit_from_size(offer.PackageSize)

        return ScrapedProductOffer(
            brand = offer.Brand,
            image = None,
            image_uri = offer.LargeImageFile,
            is_available = offer.IsAvailable or offer.InstoreIsAvailable,
            merchant_name = SupportedMerchant.WOOLWORTHS.value,
            merchant_stockcode = str(offer.Stockcode),
            name = offer.Name,
            price_now = offer.Price or offer.InstorePrice or 0,
            price_per_cup = (offer.CupString.upper() if offer.CupString else None)
                or (offer.InstoreCupString.upper() if offer.InstoreCupString else None),
            price_was = offer.WasPrice or offer.InstoreWasPrice or 0,
            size = offer.PackageSize.upper(),
            size_unit = _Unit or offer.PackageSize.upper(),
            size_value = _Value,
            web_url = f"{self.base_url}/shop/productdetails/{offer.Stockcode}"
        )

    #endregion Methods
