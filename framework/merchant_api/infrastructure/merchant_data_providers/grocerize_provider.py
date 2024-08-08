from typing import List

from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.merchant import Merchant
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from framework.merchant_api.infrastructure.merchant_data_providers.merchant_data_provider import \
    MerchantDataProvider


class GrocerizeProvider(MerchantDataProvider):

    #region ---------------- Properties ----------------

    @property
    def base_url(self) -> str:
        return 'https://grocerize.com.au'

    @property
    def priority(self) -> int:
        return 10

    @property
    def supported_merchants(self) -> List[str]:
        return [
            SupportedMerchant.COLES,
            SupportedMerchant.WOOLWORTHS
        ]

    #endregion Properties

    #region ---------------- Methods ----------------

    def get_product(self, product: DoraProduct) -> ScrapedProductOffer | None:
        pass

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        pass

    #endregion Methods
