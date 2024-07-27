import os
import random
import sys
import time
from datetime import datetime, timedelta
from typing import List

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

sys.path.append(os.getcwd())

from domain.entities.merchant import Merchant
from framework.merchant_api.domain.entities.aldi_product_offer import \
    AldiProductOffer
from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from framework.merchant_api.services.imerchant_data_provider import \
    IMerchantDataProvider


class AldiProvider(IMerchantDataProvider):

    #region ---------------- Fields ----------------

    _cached_offers: List[ScrapedProductOffer] = []

    _cached_offers_last_updated: datetime = datetime(2000, 1, 1)

    _is_healthy = True

    #endregion Fields

    #region ---------------- Properties ----------------

    @property
    def base_url(self) -> str:
        return 'https://www.aldi.com.au'

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
            SupportedMerchant.ALDI
        ]

    #endregion Properties

    #region ---------------- Methods ----------------

    def get_product(self, product: DoraProduct) -> ScrapedProductOffer:
        _CacheOlderThanAWeek = datetime.now() - self._cached_offers_last_updated > timedelta(days=7)
        if not self._cached_offers or _CacheOlderThanAWeek:
            self._update_cache()

        return next(_Offer for _Offer in self._cached_offers if _Offer.name == product.name)

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        _ScrapedProductOffers = []

        _CacheOlderThanAWeek = datetime.now() - self._cached_offers_last_updated > timedelta(days=7)
        if not self._cached_offers or _CacheOlderThanAWeek:
            self._update_cache()

        for _Offer in self._cached_offers:
            _MinimumSimilarity = 70
            _SimilarityScore = self._calculate_similarity_score(_Offer.name, search_term, _MinimumSimilarity)
            _MinimumScore = len(search_term.split()) * _MinimumSimilarity

            if _SimilarityScore >= _MinimumScore:
                _ScrapedProductOffers.append(_Offer)

            if len(_ScrapedProductOffers) >= result_limit:
                return _ScrapedProductOffers

        return _ScrapedProductOffers

    def _calculate_similarity_score(self, product_name: str, search_term: str, min_similarity: int) -> int:
        _SearchWords = search_term.lower().split()
        _ProductWords = product_name.lower().split()
        _Score = 0

        for _ProductWord in _ProductWords:
            for _SearchWord in _SearchWords:
                _Similarity = fuzz.ratio(_ProductWord, _SearchWord)
                if _Similarity >= min_similarity:
                    _Score += _Similarity

        return _Score

    def _translate_offer(self, offer: AldiProductOffer) -> ScrapedProductOffer:
        _Value, _Unit = ScrapedProductOffer.get_size(offer.amount)

        return ScrapedProductOffer(
            brand = None,
            image = None,
            image_uri = offer.image_uri,
            is_available = True,
            merchant_name = SupportedMerchant.ALDI.value,
            merchant_stockcode = None,
            name = offer.description.rstrip(offer.amount).strip(),
            price_now = float(offer.current_price_value.lstrip('$').rstrip('c') + offer.current_price_decimal),
            price_per_cup = offer.unit_price,
            price_was = float(offer.former_price.lstrip('$').rstrip('c') or 0),
            size = offer.amount,
            size_unit = _Unit or offer.amount.upper(),
            size_value = _Value,
            web_url = offer.product_url
        )

    def _update_cache(self) -> None:
        for _Category in [
            'baby/baby-food',
            'baby/nappies-and-wipes',
            'beauty',
            'freezer',
            'fresh-produce',
            'fresh-produce/dairy-eggs',
            'healthy',
            'laundry-household/household',
            'laundry-household/laundry',
            'limited-time-only',
            'liquor/beer-cider',
            'liquor/champagne-sparkling',
            'liquor/spirits',
            'liquor/spirits',
            'liquor/wine',
            'pantry/chocolate',
            'pantry/coffee',
            'pantry/olive-oil',
            'pet-supplies',
            'pet-supplies',
            'price-reductions',
            'super-savers'
        ]:
            _Response = requests.get(f"https://www.aldi.com.au/groceries/{_Category}/")
            _Soup = BeautifulSoup(_Response.content, features="html.parser")
            _PageSearchResult = _Soup.find_all('a', class_='box--wrapper')

            for _ProductSearchResult in _PageSearchResult:
                self._cached_offers.append(
                    self._translate_offer(
                        AldiProductOffer(
                            amount = _ProductSearchResult.find('span', class_='box--amount').text.strip()
                                if _ProductSearchResult.find('span', class_='box--amount') else "",
                            current_price_decimal = _ProductSearchResult.find('span', class_='box--decimal').text.strip()
                                if _ProductSearchResult.find('span', class_='box--decimal') else "0",
                            current_price_value = _ProductSearchResult.find('span', class_='box--value').text.strip()
                                if _ProductSearchResult.find('span', class_='box--value') else "0",
                            description = _ProductSearchResult.find('div', class_='box--description--header').text.strip()
                                if _ProductSearchResult.find('div', class_='box--description--header') else "",
                            former_price = _ProductSearchResult.find('span', class_='box--former-price').text.strip()
                                if _ProductSearchResult.find('span', class_='box--former-price') else "0",
                            image_uri = _ProductSearchResult.find('img')['src'].strip()
                                if _ProductSearchResult.find('img') else None,
                            product_url = _ProductSearchResult['href'].strip()
                                if _ProductSearchResult['href'] else None,
                            unit_price = _ProductSearchResult.find('span', class_='box--baseprice').text.strip()
                                if _ProductSearchResult.find('span', class_='box--baseprice') else "",
                        )
                    )
                )

            time.sleep(random.uniform(0, 0.5))

        self._cached_offers_last_updated = datetime.now()

    #endregion Methods
