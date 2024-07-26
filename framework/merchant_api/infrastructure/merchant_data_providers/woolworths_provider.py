import random
import time
import urllib.parse
from typing import List

from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.merchant import Merchant
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from framework.merchant_api.domain.entities.woolworths_product_offer import \
    WoolworthsProductOffer
from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from framework.merchant_api.infrastructure.session import get_cached_session
from framework.merchant_api.services.imerchant_data_provider import \
    IMerchantDataProvider


class WoolworthsProvider(IMerchantDataProvider):

    #region ---------------- Fields ----------------

    _is_healthy = True

    #endregion Fields

    #region ---------------- Properties ----------------

    @property
    def base_url(self) -> str:
        return 'https://www.woolworths.com.au/'

    @property
    def is_healthy(self) -> bool:
        return self._is_healthy

    @is_healthy.setter
    def is_healthy(self, val: bool) -> None:
        self._is_healthy = val

    @property
    def priority(self) -> int:
        return 1

    @property
    def supported_merchants(self) -> List[str]:
        return [
            SupportedMerchant.WOOLWORTHS
        ]

    #endregion Properties

    #region ---------------- Methods ----------------

    def get_product(self, product: DoraProduct) -> ScrapedProductOffer:
        with get_cached_session() as _Session:
            _Url = 'https://www.woolworths.com.au/apis/ui/Search/products'
            _Body = {
                'Location': f'/shop/search/products?{urllib.parse.urlencode({"searchTerm": product.merchant_stockcode})}',
                'PageNumber': 1,
                'PageSize': 36,
                'SearchTerm': product.merchant_stockcode,
                'SortType': "TraderRelevance"
            }

            _PageSearchResult = _Session.post(_Url, json=_Body).json()

            return self._translate_offer(
                WoolworthsProductOffer.model_construct(**_PageSearchResult['Products'][0]['Products'][0])
            )

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        with get_cached_session() as _Session:
            _Session.get('https://www.woolworths.com.au')
            _Url = 'https://www.woolworths.com.au/apis/ui/Search/products'
            _Body = {
                'Filters': [],
                'IsSpecial': False,
                'Location': f'/shop/search/products?{urllib.parse.urlencode({"searchTerm": search_term})}',
                'PageNumber': 1,
                'PageSize': 36,
                'SearchTerm': search_term,
                'SortType': "TraderRelevance"
            }

            _ScrapedProductOffers = []
            while True:
                _PageSearchResult = _Session.post(_Url, json=_Body).json()

                if not _PageSearchResult['Products']:
                    return _ScrapedProductOffers

                for _ProductSearchResult in _PageSearchResult['Products']:
                    _ScrapedProductOffers.append(
                        self._translate_offer(
                            WoolworthsProductOffer.model_construct(**_ProductSearchResult['Products'][0])
                        )
                    )

                    if len(_ScrapedProductOffers) >= result_limit:
                        return _ScrapedProductOffers

                _Body['PageNumber'] += 1
                time.sleep(random.uniform(0, 2))

    def _translate_offer(self, offer: WoolworthsProductOffer) -> ScrapedProductOffer:
        _Value, _Unit = ScrapedProductOffer.get_size(offer.PackageSize)

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
            web_url = f"https://www.woolworths.com.au/shop/productdetails/{offer.Stockcode}"
        )

    #endregion Methods
