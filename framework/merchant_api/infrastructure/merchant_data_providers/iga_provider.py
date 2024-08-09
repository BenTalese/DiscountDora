import random
import time
from typing import List

from clapy import IServiceProvider
from flask import current_app

from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.iga_product_offer import \
    IGAProductOffer
from framework.merchant_api.domain.entities.merchant import Merchant
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from framework.merchant_api.infrastructure.session import get_cached_session
from framework.merchant_api.services.iconfiguration_manager import \
    IConfigurationManager
from framework.merchant_api.services.imerchant_data_provider import \
    IMerchantDataProvider


class IGAProvider(IMerchantDataProvider):

    #region ---------------- Properties ----------------

    @property
    def base_url(self) -> str:
        return 'https://www.igashop.com.au'

    @property
    def priority(self) -> int:
        return 1

    @property
    def supported_merchants(self) -> List[str]:
        return [
            SupportedMerchant.IGA
        ]

    #endregion Properties

    #region ---------------- Methods ----------------

    def get_product(self, product: DoraProduct) -> ScrapedProductOffer | None:
        _ServiceProvider: IServiceProvider = current_app.service_provider
        _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)
        _StoreID = _ConfigurationManager.get_iga_store_id()

        with get_cached_session() as _Session:
            _Url = f"{self.base_url}/api/storefront/stores/{_StoreID}/products/{product.merchant_stockcode}"
            _Response = _Session.get(_Url).json()

            if not _Response:
                return None

            return self._translate_offer(IGAProductOffer.model_validate(_Response))

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        _ServiceProvider: IServiceProvider = current_app.service_provider
        _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)
        _StoreID = _ConfigurationManager.get_iga_store_id()

        with get_cached_session() as _Session:
            _Url = f'{self.base_url}/api/storefront/stores/{_StoreID}/search'
            _Params = {
                'q': search_term[:50],  # no results if query > 50
                'skip': 0,
                'take': result_limit
            }

            _ScrapedProductOffers = []
            _StartTime = time.time()
            _MaxAttemptTime = 15  # seconds

            while time.time() - _StartTime < _MaxAttemptTime:
                _PageSearchResult = _Session.get(_Url, _Params).json()

                if not _PageSearchResult['items']:
                    return _ScrapedProductOffers

                for _ProductSearchResult in _PageSearchResult['items']:
                    _ScrapedProductOffers.append(
                        self._translate_offer(
                            IGAProductOffer.model_validate(_ProductSearchResult)
                        )
                    )

                    if len(_ScrapedProductOffers) >= result_limit:
                        return _ScrapedProductOffers

                _Params['skip'] += _Params['take']
                time.sleep(random.uniform(0, 2))

    def _translate_offer(self, offer: IGAProductOffer) -> ScrapedProductOffer:
        return ScrapedProductOffer(
            brand = offer.brand,
            image = None,
            image_uri = offer.image['default'],
            is_available = offer.available,
            merchant_name = SupportedMerchant.IGA.value,
            merchant_stockcode = offer.productId,
            name = offer.name,
            price_now = offer.priceNumeric or 0,
            price_per_cup = offer.pricePerUnit,
            price_was = offer.wasPriceNumeric or 0,
            size = str(offer.unitOfSize.size) + offer.unitOfSize.abbreviation,
            size_unit = offer.unitOfSize.abbreviation,
            size_value = float(offer.unitOfSize.size),
            web_url = f"{self.base_url}/product/{'-'.join(offer.name.lower().split()) + '-' + offer.productId}"
        )

    #endregion Methods
