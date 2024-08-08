import random
import time
from typing import List

from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.merchant import Merchant
from framework.merchant_api.domain.entities.save_on_groceries_product_offer import \
    SaveOnGroceriesProductOffer
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from framework.merchant_api.infrastructure.session import get_cached_session
from framework.merchant_api.infrastructure.merchant_data_providers.merchant_data_provider import \
    MerchantDataProvider


class SaveOnGroceriesProvider(MerchantDataProvider):

    #region ---------------- Fields ----------------

    _get_merchant_stockcode_func_mapping = {
        SupportedMerchant.ALDI: lambda url: None,
        SupportedMerchant.COLES: lambda url: url.rsplit('/', 1)[-1],
        SupportedMerchant.IGA: lambda url: url.rsplit('-', 1)[-1],
        SupportedMerchant.WOOLWORTHS: lambda url: url.rsplit('/', 2)[-2]
    }

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
        return 5

    @property
    def supported_merchants(self) -> List[str]:
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
            _ShopID = self._merchant_id_mapping.get(product.merchant_name)
            _Url = f'{self.base_url}/search-in-store?query={product.name}&shop_id={_ShopID}&page={1}'
            _PageSearchResult = _Session.get(_Url).json()['products']['data']

            if not _PageSearchResult:
                return None

            return self._translate_offer(
                SaveOnGroceriesProductOffer.model_validate(_PageSearchResult[0]),
                product.merchant_name
            )

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        with get_cached_session() as _Session:
            _Page = 1
            _ShopID = self._merchant_id_mapping.get(merchant.name)
            _Url = f'{self.base_url}/search-in-store?query={search_term}&shop_id={_ShopID}&page={_Page}'

            _ScrapedProductOffers = []
            _StartTime = time.time()
            _MaxAttemptTime = 15  # seconds

            while time.time() - _StartTime < _MaxAttemptTime:
                _PageSearchResult = _Session.get(_Url).json()['products']['data']

                if not _PageSearchResult:
                    return _ScrapedProductOffers

                for _ProductSearchResult in _PageSearchResult:
                    _ScrapedProductOffers.append(
                        self._translate_offer(
                            SaveOnGroceriesProductOffer.model_validate(_ProductSearchResult),
                            merchant.name
                        )
                    )

                    if len(_ScrapedProductOffers) >= result_limit:
                        return _ScrapedProductOffers

                _Page += 1
                _Url[:-1] + ''
                time.sleep(random.uniform(0, 2))

    def _translate_offer(self, offer: SaveOnGroceriesProductOffer, merchant_name: SupportedMerchant) -> ScrapedProductOffer:
        _Value, _Unit = ScrapedProductOffer._extract_value_and_unit_from_size(offer.product_package_size)

        return ScrapedProductOffer(
            brand = None,
            image = None,
            image_uri = offer.product_image_url,
            is_available = True,
            merchant_name = merchant_name.value,
            merchant_stockcode = self._get_merchant_stockcode_func_mapping.get(merchant_name)(offer.product_url),
            name = offer.name,
            price_now = offer.price,
            price_per_cup = offer.product_price_per_amount,
            price_was = offer.price - offer.product_price_saving,
            size = offer.product_package_size.upper(),
            size_unit = _Unit or offer.product_package_size.upper(),
            size_value = _Value,
            web_url = offer.product_url
        )

    #endregion Methods
