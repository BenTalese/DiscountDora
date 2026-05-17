import logging
import random
import time
from typing import List

from pydantic import ValidationError

from merchant_api.domain.entities.dora_product import DoraProduct
from merchant_api.domain.entities.merchant import Merchant
from merchant_api.domain.entities.save_on_groceries_product_offer import \
    SaveOnGroceriesProductOffer
from merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from merchant_api.infrastructure.merchant_data_providers.merchant_data_provider import \
    MerchantDataProvider
from merchant_api.infrastructure.session import get_cached_session


class SaveOnGroceriesProvider(MerchantDataProvider):

    #region ---------------- Fields ----------------

    _logger = logging.getLogger(__name__)

    _merchant_id_mapping = {
        SupportedMerchant.ALDI: 1,
        SupportedMerchant.COLES: 4,
        SupportedMerchant.IGA: 3,
        SupportedMerchant.WOOLWORTHS: 2
    }

    #endregion Fields

    #region ---------------- Properties ----------------

    @property
    def base_url(self) -> str:
        return 'https://www.saveongroceries.com.au'

    @property
    def priority(self) -> int:
        return 10

    @property
    def supported_merchants(self) -> List[SupportedMerchant]:
        return [
            SupportedMerchant.ALDI,
            SupportedMerchant.COLES,
            SupportedMerchant.IGA,
            SupportedMerchant.WOOLWORTHS
        ]

    #endregion Properties

    #region ---------------- Methods ----------------

    def get_product(self, product: DoraProduct) -> ScrapedProductOffer | None:
        with get_cached_session() as _Session:
            _ShopID = self._merchant_id_mapping.get(SupportedMerchant(product.merchant_name))
            _Url = f'{self.base_url}/search-in-store?query={product.name}&shop_id={_ShopID}&page={1}'
            _PageSearchResult = _Session.get(_Url).json()['products']['data']

            if not _PageSearchResult:
                return None

            try:
                return self._translate_offer(
                    SaveOnGroceriesProductOffer.model_validate(_PageSearchResult[0]),
                    SupportedMerchant(product.merchant_name)
                )

            except ValidationError as e:
                for _Error in e.errors():
                    self._logger.exception(
                        f"Pydantic error in {_Error['loc']}: {_Error['msg']}, received value: {_Error['input']}"
                    )

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        _Page = 1
        _ShopID = self._merchant_id_mapping.get(merchant.name)
        _Url = f'{self.base_url}/search-in-store?query={search_term}&shop_id={_ShopID}&page={_Page}'

        _ScrapedProductOffers: List[ScrapedProductOffer] = []
        _StartTime = time.time()

        with get_cached_session() as _Session:
            while time.time() - _StartTime < self._max_attempt_time_seconds:
                _PageSearchResult = _Session.get(_Url).json()['products']

                if not _PageSearchResult['data']:
                    return _ScrapedProductOffers

                for _ProductSearchResult in _PageSearchResult['data']:
                    try:
                        _ScrapedProductOffers.append(
                            self._translate_offer(
                                SaveOnGroceriesProductOffer.model_validate(_ProductSearchResult),
                                merchant.name
                            )
                        )

                    except ValidationError as e:
                        for _Error in e.errors():
                            self._logger.exception(
                                f"Pydantic error in {_Error['loc']}: {_Error['msg']}, received value: {_Error['input']}"
                            )

                    if len(_ScrapedProductOffers) >= result_limit:
                        return _ScrapedProductOffers

                if _PageSearchResult['next_page_url'] is None:
                    return _ScrapedProductOffers

                _Url = _PageSearchResult['next_page_url']
                time.sleep(random.uniform(0, self._max_backoff_time_seconds))

            self._logger.info(f"Merchant data provider '{self.base_url}' timed out searching for '{search_term}'.")
            return _ScrapedProductOffers

    def _translate_offer(self, offer: SaveOnGroceriesProductOffer, merchant_name: SupportedMerchant) -> ScrapedProductOffer:
        _Value, _Unit = ScrapedProductOffer._extract_value_and_unit_from_size(offer.product_package_size)

        match merchant_name:
            case SupportedMerchant.COLES:
                offer.product_url = offer.product_url.rsplit('/', 1)[-1]
            case SupportedMerchant.IGA:
                offer.product_url = offer.product_url.rsplit('-', 1)[-1]
            case SupportedMerchant.WOOLWORTHS:
                offer.product_url = offer.product_url.rsplit('/', 2)[-2]
            case _:
                raise Exception(f"Unsupported merchant name '{merchant_name}' for offer translation.")

        return ScrapedProductOffer(
            brand = None,
            image = None,
            image_uri = offer.product_image_url,
            is_available = True,
            merchant_name = merchant_name.value,
            merchant_stockcode = offer.product_url,
            name = offer.name.rstrip(offer.product_package_size),
            price_now = offer.price,
            price_per_cup = offer.product_price_per_amount,
            price_was = (offer.price + offer.product_price_saving) if offer.product_price_saving > 0 else 0,
            size = offer.product_package_size.upper(),
            size_unit = _Unit or offer.product_package_size.upper(),
            size_value = _Value,
            web_url = offer.product_url
        )

    #endregion Methods
