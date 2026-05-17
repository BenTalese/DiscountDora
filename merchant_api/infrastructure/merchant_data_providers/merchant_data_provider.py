from abc import ABC, abstractmethod

from merchant_api.domain.entities.dora_product import DoraProduct
from merchant_api.domain.entities.merchant import Merchant
from merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant


class MerchantDataProvider(ABC):

    #region ---------------- Fields ----------------

    _is_healthy: bool = True

    _max_attempt_time_seconds: int = 15

    _max_backoff_time_seconds: int = 2

    #endregion Fields

    #region ---------------- Properties ----------------

    @property
    @abstractmethod
    def base_url(self) -> str:
        pass

    @property
    def is_healthy(self) -> bool:
        return self._is_healthy

    @is_healthy.setter
    def is_healthy(self, val: bool) -> None:
        self._is_healthy = val

    @property
    @abstractmethod
    def priority(self) -> int:
        pass

    @property
    @abstractmethod
    def supported_merchants(self) -> list[SupportedMerchant]:
        pass

    #endregion Properties

    #region ---------------- Methods ----------------

    @abstractmethod
    def get_product(self, product: DoraProduct) -> ScrapedProductOffer | None:
        pass

    def is_merchant_supported(self, merchant: Merchant) -> bool:
        return merchant.name in self.supported_merchants

    @abstractmethod
    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> list[ScrapedProductOffer]:
        pass

    #endregion Methods
