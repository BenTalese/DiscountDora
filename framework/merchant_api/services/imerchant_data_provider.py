from abc import ABC, abstractmethod
from typing import List

from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.merchant import Merchant
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer


class IMerchantDataProvider(ABC):

    #region ---------------- Fields ----------------

    _is_healthy = True

    #endregion Fields

    #region ---------------- Properties ----------------

    @property
    @abstractmethod
    def base_url(self) -> str:
        pass

    @property
    @abstractmethod
    def is_healthy(self) -> bool:
        return self._is_healthy

    @is_healthy.setter
    @abstractmethod
    def is_healthy(self, val: bool) -> None:
        self._is_healthy = val
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        pass

    @property
    @abstractmethod
    def supported_merchants(self) -> List[str]:
        pass

    #endregion Properties

    #region ---------------- Methods ----------------

    @abstractmethod
    def get_product(self, product: DoraProduct) -> ScrapedProductOffer | None:
        pass

    @abstractmethod
    def is_merchant_supported(self, merchant: Merchant) -> bool:
        return merchant.name in self.supported_merchants

    @abstractmethod
    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        pass

    #endregion Methods
