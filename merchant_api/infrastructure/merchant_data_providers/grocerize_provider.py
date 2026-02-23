import logging
import random
import time
from typing import List

from pydantic import ValidationError

from merchant_api.domain.entities.dora_product import DoraProduct
from merchant_api.domain.entities.grocerize_product_offer import \
    GrocerizeProductOffer
from merchant_api.domain.entities.merchant import Merchant
from merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from merchant_api.infrastructure.session import get_cached_session
from merchant_api.services.imerchant_data_provider import IMerchantDataProvider


class GrocerizeProvider(IMerchantDataProvider):

    #region ---------------- Fields ----------------

    _get_product_url_func_mapping = {
        1: lambda product_id: f'https://www.coles.com.au/product/{product_id}',
        2: lambda product_id: f'https://www.woolworths.com.au/shop/productdetails/{product_id}'
    }

    _logger = logging.getLogger(__name__)

    _merchant_id_mapping = {
        1: SupportedMerchant.COLES.value,
        2: SupportedMerchant.WOOLWORTHS.value
    }

    #endregion Fields

    #region ---------------- Properties ----------------

    @property
    def base_url(self) -> str:
        return 'https://grocerize-backend.fly.dev'

    @property
    def priority(self) -> int:
        return 5

    @property
    def supported_merchants(self) -> List[str]:
        return [
            SupportedMerchant.COLES,
            SupportedMerchant.WOOLWORTHS
        ]

    #endregion Properties

    #region ---------------- Methods ----------------

    def get_product(self, product: DoraProduct) -> ScrapedProductOffer | None:
        with get_cached_session() as _Session:
            _Url = f'{self.base_url}/search?q={product.name}&'
            _PageSearchResult = _Session.get(_Url).json()

            if not _PageSearchResult:
                return None

            _SortedOffers = sorted(_PageSearchResult['items'], key=lambda item: not item['has_exact_match'])

            try:
                _Offers = self._translate_offers(
                    GrocerizeProductOffer.model_validate(_SortedOffers[0]),
                )
            except ValidationError as e:
                for _Error in e.errors():
                    self._logger.exception(
                        f"Pydantic error in {_Error['loc']}: {_Error['msg']}, received value: {_Error['input']}"
                    )

            return next((_Offer for _Offer in _Offers if _Offer.merchant_name == product.merchant_name), None)

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        _Page = 2
        _Url = f'{self.base_url}/search?q={search_term}&'

        _ScrapedProductOffers: List[ScrapedProductOffer] = []
        _StartTime = time.time()

        with get_cached_session() as _Session:
            while time.time() - _StartTime < self._max_attempt_time_seconds:
                _PageSearchResult = _Session.get(_Url).json()

                if not _PageSearchResult or not _PageSearchResult['items']:
                    return _ScrapedProductOffers

                for _ProductSearchResult in _PageSearchResult['items']:
                    try:
                        _Offer = self._translate_offer(
                            GrocerizeProductOffer.model_validate(_ProductSearchResult),
                            merchant.name
                        )

                        if _Offer:
                            _ScrapedProductOffers.append(_Offer)

                    except ValidationError as e:
                        for _Error in e.errors():
                            self._logger.exception(
                                f"Pydantic error in {_Error['loc']}: {_Error['msg']}, received value: {_Error['input']}"
                            )

                    if len(_ScrapedProductOffers) >= result_limit:
                        return _ScrapedProductOffers

                if 'page' not in _Url:
                    _Url += f"&page=2&currentItemId={str(_PageSearchResult['currentItemId'])}"
                else:
                    _Url = f"{_Url.split('page')[0]}page={_Page}&currentItemId={str(_PageSearchResult['currentItemId'])}"

                _Page += 1
                time.sleep(random.uniform(0, self._max_backoff_time_seconds))

            self._logger.info(f"Merchant data provider '{self.base_url}' timed out searching for '{search_term}'.")
            return _ScrapedProductOffers

    def _translate_offer(self, offer_grouping: GrocerizeProductOffer, merchant_name: SupportedMerchant) -> ScrapedProductOffer | None:
        for _Offer in offer_grouping.item_pricing:
            if self._merchant_id_mapping.get(_Offer.vendor_id) == merchant_name.value:
                _Value, _Unit = ScrapedProductOffer._extract_value_and_unit_from_size(_Offer.volume)

                return ScrapedProductOffer(
                    brand = None,
                    image = None,
                    image_uri = offer_grouping.image_url,
                    is_available = _Offer.available,
                    merchant_name = self._merchant_id_mapping.get(_Offer.vendor_id),
                    merchant_stockcode = _Offer.vendor_product_code,
                    name = offer_grouping.name.rstrip(_Offer.volume),
                    price_now = _Offer.price,
                    price_per_cup = f'${_Offer.cup_price} / {_Offer.cup_volume.upper()}'
                        if _Offer.cup_price and _Offer.cup_volume else None,
                    price_was = _Offer.special_original_price or 0,
                    size = _Offer.volume.upper(),
                    size_unit = _Unit or _Offer.volume.upper(),
                    size_value = _Value,
                    web_url = self._get_product_url_func_mapping.get(_Offer.vendor_id)(_Offer.vendor_product_code)
                )

    #endregion Methods
