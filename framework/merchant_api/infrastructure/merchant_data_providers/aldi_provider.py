import json
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz


# from framework.merchant_api.services.iproduct_image_provider import IProductImageProvider

sys.path.append(os.getcwd())
from framework.merchant_api.infrastructure.configuration_manager import ConfigurationManager
from framework.merchant_api.services.iconfiguration_manager import \
    IConfigurationManager

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

    _aldi_products_by_category: Dict[str, List[str]]

    _cached_offers_by_category: Dict[str, List[ScrapedProductOffer]] = {}

    _cached_offers_last_updated_by_category: Dict[str, datetime] = {}

    _is_healthy = True

    #endregion Fields

    #region ---------------- Constructors ----------------

    def __init__(self):
        _CategoriesJson = Path(__file__).parent / 'aldi_products_by_category.json'
        with _CategoriesJson.open('r') as _File:
            self._aldi_products_by_category = json.load(_File)

        # Add dynamic categories (products always changing)
        self._aldi_products_by_category['limited-time-only'] = []
        self._aldi_products_by_category['price-reductions'] = []
        self._aldi_products_by_category['special-buys-liquor'] = []
        self._aldi_products_by_category['super-savers'] = []

        for _Category in self._aldi_products_by_category.keys():
            self._cached_offers_by_category[_Category] = []
            self._cached_offers_last_updated_by_category[_Category] = datetime(2000, 1, 1)

    #endregion Constructors

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
        _ProductCategory = next(
            _Category
            for _Category, _ProductNames
            in self._aldi_products_by_category.items()
            if product.name in _ProductNames
        )

        _IsCacheOlderThanOneWeek = datetime.now() - self._cached_offers_last_updated_by_category[_ProductCategory] > timedelta(days=7)

        if _IsCacheOlderThanOneWeek:
            self._update_category_cache(_ProductCategory)

        return next(_Offer for _Offer in self._cached_offers_by_category[_ProductCategory] if _Offer.name == product.name)

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        _ScrapedProductOffers = []

        _CategoriesToSearch = self._get_relevant_categories_to_search(search_term)

        for _Category in _CategoriesToSearch:
            _IsCacheOlderThanOneWeek = datetime.now() - self._cached_offers_last_updated_by_category[_Category] > timedelta(days=7)

            if _IsCacheOlderThanOneWeek:
                self._update_category_cache(_Category)

            for _Offer in self._cached_offers_by_category[_Category]:
                if self._is_similar_string(_Offer.name, search_term):
                    _ScrapedProductOffers.append(_Offer)

                if len(_ScrapedProductOffers) >= result_limit:
                    return _ScrapedProductOffers

        return _ScrapedProductOffers

    def _is_similar_string(self, string1: str, string2: str) -> int:
        _MinimumSimilarity = 70
        _String1Words = string2.lower().split()
        _String2Words = string1.lower().split()
        _Score = 0

        for _String2Word in _String2Words:
            for _String1Word in _String1Words:
                _Similarity = fuzz.ratio(_String2Word, _String1Word)
                if _Similarity >= _MinimumSimilarity:
                    _Score += _Similarity

        _MinimumScore = len(string2.split()) * _MinimumSimilarity

        if _Score >= _MinimumScore:
            return True

        return False

    def _get_relevant_categories_to_search(self, search_term: str) -> List[str]:
        _CategoriesWithRelevancyScore: List[Tuple[str, int]] = []
        for _Category in self._aldi_products_by_category.keys():
            _ProductsInCategory = self._aldi_products_by_category[_Category]
            _RelevancyScore = 0

            for _ProductName in _ProductsInCategory:
                if self._is_similar_string(_ProductName, search_term):
                    _RelevancyScore += 1

            if _RelevancyScore > 0:
                _CategoriesWithRelevancyScore.append((_Category, _RelevancyScore))

        _CategoriesOrderedByRelevance = [
            _Category
            for _Category, _Score
            in sorted(_CategoriesWithRelevancyScore, key = lambda cr: cr[1], reverse = True)
        ]

        # Add dynamic categories (products always changing)
        _CategoriesOrderedByRelevance.append('limited-time-only')
        _CategoriesOrderedByRelevance.append('price-reductions')
        _CategoriesOrderedByRelevance.append('special-buys-liquor')
        _CategoriesOrderedByRelevance.append('super-savers')

        return _CategoriesOrderedByRelevance

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

    def _update_category_cache(self, category: str) -> None:
        # Should cached products be saved as json file as well? seems beneficial... so it doesn't
        # need to rebuild cache from scratch, will need to save last time updated, maybe in file name
        # Atif idea: use NOSQL database to store offers
        _Response = requests.get(f"https://www.aldi.com.au/groceries/{category}/")
        _Soup = BeautifulSoup(_Response.content, features="html.parser")
        _PageSearchResult = _Soup.find_all('a', class_='box--wrapper')

        self._cached_offers_by_category[category].clear()

        for _ProductSearchResult in _PageSearchResult:
            self._cached_offers_by_category[category].append(
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

        time.sleep(random.uniform(0, 2))
        self._cached_offers_last_updated_by_category[category] = datetime.now()

    #endregion Methods


if __name__ == "__main__":
    x = AldiProvider(ConfigurationManager())
    t1 = time.time()
    g = x.search_by_term("Fruit Snack Cereal Bars", {}, 1)
    t2 = time.time()
    dif1 = t2 - t1

    t3 = time.time()
    h = x.search_by_term("Fruit Snack Cereal Bars", {}, 1)
    t4 = time.time()
    dif2 = t4 - t3
    y = 0
