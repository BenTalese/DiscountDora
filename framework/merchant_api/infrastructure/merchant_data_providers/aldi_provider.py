import json
import logging
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
from bs4 import BeautifulSoup, ResultSet
from pydantic import ValidationError

from domain.entities.merchant import Merchant
from framework.merchant_api.domain.entities.aldi_product_offer import \
    AldiProductOffer
from framework.merchant_api.domain.entities.dora_product import DoraProduct
from framework.merchant_api.domain.entities.scraped_product_offer import \
    ScrapedProductOffer
from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant
from framework.merchant_api.infrastructure.similarity import is_similar_phrase
from framework.merchant_api.services.imerchant_data_provider import \
    IMerchantDataProvider


class AldiProvider(IMerchantDataProvider):

    #region ---------------- Fields ----------------

    _aldi_product_names_by_category: Dict[str, List[str]]

    _cached_offers_by_category: Dict[str, List[ScrapedProductOffer]] = {}

    _cached_offers_last_updated_by_category: Dict[str, datetime] = {}

    _logger: logging.Logger = logging.getLogger(__name__)

    _similarity_threshold: int = 70

    #endregion Fields

    #region ---------------- Constructors ----------------

    def __init__(self):
        _CategoriesJson = Path(__file__).parent / 'aldi_products_by_category.json'
        with _CategoriesJson.open('r') as _File:
            self._aldi_product_names_by_category = json.load(_File)

        # Add dynamic categories (products always changing)
        self._aldi_product_names_by_category['limited-time-only'] = []
        self._aldi_product_names_by_category['price-reductions'] = []
        self._aldi_product_names_by_category['special-buys-liquor'] = []
        self._aldi_product_names_by_category['super-savers'] = []

        for _Category in self._aldi_product_names_by_category.keys():
            self._cached_offers_by_category[_Category] = []
            self._cached_offers_last_updated_by_category[_Category] = datetime(2000, 1, 1)

    #endregion Constructors

    #region ---------------- Properties ----------------

    @property
    def base_url(self) -> str:
        return 'https://www.aldi.com.au'

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

    def get_product(self, product: DoraProduct) -> ScrapedProductOffer | None:
        _ProductCategory = next(
            _Category
            for _Category, _ProductNames
            in self._aldi_product_names_by_category.items()
            if product.name in _ProductNames
        )

        _IsCacheOlderThanOneWeek = datetime.now() - self._cached_offers_last_updated_by_category[_ProductCategory] > timedelta(days=7)

        if _IsCacheOlderThanOneWeek:
            self._update_category_cache(_ProductCategory)

        return next(_Offer for _Offer in self._cached_offers_by_category[_ProductCategory] if _Offer.name == product.name)

    def search_by_term(self, search_term: str, merchant: Merchant, result_limit: int) -> List[ScrapedProductOffer]:
        _ScrapedProductOffers: List[ScrapedProductOffer] = []

        _CategoriesToSearch = self._get_relevant_categories_to_search(search_term)

        for _Category in _CategoriesToSearch:
            _IsCacheOlderThanOneWeek = datetime.now() - self._cached_offers_last_updated_by_category[_Category] > timedelta(days=7)

            if _IsCacheOlderThanOneWeek:
                self._update_category_cache(_Category)

            for _Offer in self._cached_offers_by_category[_Category]:
                if is_similar_phrase(search_term, _Offer.name, self._similarity_threshold):
                    _ScrapedProductOffers.append(_Offer)

                if len(_ScrapedProductOffers) >= result_limit:
                    return _ScrapedProductOffers

        return _ScrapedProductOffers

    def _extract_from_html(self, html: ResultSet[Any], element: str, cls: str, default_value: Any):
        if _Value := html.find(element, class_=cls):
            return _Value.text.strip()
        else:
            return default_value

    def _get_relevant_categories_to_search(self, search_term: str) -> List[str]:
        _CategoriesWithRelevancyScore: List[Tuple[str, int]] = []
        for _Category in self._aldi_product_names_by_category.keys():
            _ProductsInCategory = self._aldi_product_names_by_category[_Category]
            _RelevancyScore = 0

            for _ProductName in _ProductsInCategory:
                if is_similar_phrase(search_term, _ProductName, self._similarity_threshold):
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
        _Value, _Unit = ScrapedProductOffer._extract_value_and_unit_from_size(offer.amount)

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
        _Response = requests.get(f"{self.base_url}/groceries/{category}/")
        _Soup = BeautifulSoup(_Response.content, features="html.parser")
        _PageSearchResult = _Soup.find_all('a', class_='box--wrapper')

        self._cached_offers_by_category[category].clear()

        for _ProductSearchResult in _PageSearchResult:
            try:
                self._cached_offers_by_category[category].append(
                    self._translate_offer(
                        AldiProductOffer(
                            amount = self._extract_from_html(_ProductSearchResult, 'span', 'box--amount', ""),
                            current_price_decimal = self._extract_from_html(_ProductSearchResult, 'span', 'box--decimal', "0"),
                            current_price_value = self._extract_from_html(_ProductSearchResult, 'span', 'box--value', "0"),
                            description = self._extract_from_html(_ProductSearchResult, 'div', 'box--description--header', ""),
                            former_price = self._extract_from_html(_ProductSearchResult, 'span', 'box--former-price', "0"),
                            image_uri = _ProductSearchResult.find('img')['src'].strip()
                                if _ProductSearchResult.find('img') else None,
                            product_url = _ProductSearchResult['href'].strip()
                                if _ProductSearchResult['href'] else None,
                            unit_price = self._extract_from_html(_ProductSearchResult, 'span', 'box--baseprice', "")
                        )
                    )
                )

            except ValidationError as e:
                for _Error in e.errors():
                    self._logger.exception(
                        f"Pydantic error in {_Error['loc']}: {_Error['msg']}, received value: {_Error['input']}"
                    )

        time.sleep(random.uniform(0, self._max_backoff_time_seconds))
        self._cached_offers_last_updated_by_category[category] = datetime.now()

    #endregion Methods
