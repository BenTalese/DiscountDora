import json

from bs4 import BeautifulSoup
from requests_cache import CachedSession

from framework.merchant_api.domain.entities.coles_product_offer import \
    ColesProductOffer


def get_by_stockcode(session: CachedSession, response_text: str, stockcode: str, product_name: str):
    _Soup = BeautifulSoup(response_text, features="html.parser")
    _BuildID = json.loads(_Soup.find(id='__NEXT_DATA__').contents[0])['buildId']

    _Url = f'https://www.coles.com.au/_next/data/{_BuildID}/en/search.json'
    _Params = {
        'q': product_name,
        'page': 1
    }

    _PageSearchResult = session.get(_Url, _Params).json()['pageProps']['searchResults']
    for _ProductSearchResult in _PageSearchResult['results']:
        if _ProductSearchResult['_type'] == "PRODUCT" and str(_ProductSearchResult["id"]) == stockcode:
            return ColesProductOffer.model_validate(_ProductSearchResult)


def search(session: CachedSession, search_term: str, start_page: int, max_page: int, max_results: int):
    _Response = session.get('https://www.coles.com.au/')
    _Soup = BeautifulSoup(_Response.text, features="html.parser")
    _BuildID = json.loads(_Soup.find(id='__NEXT_DATA__').contents[0])['buildId']

    _Url = f'https://www.coles.com.au/_next/data/{_BuildID}/en/search.json'
    _Params = {
        'q': search_term,
        'page': start_page
    }
    # if specials_only:
    #     params['filter_Special'] = 'all'

    _SuggestedTerm: str = None
    _ResultCount = 0
    while True:
        _PageSearchResult = session.get(_Url, _Params).json()['pageProps']['searchResults']
        # TODO: Return out of use case as separate parameter
        # TODO: suggested term is a list?
        _SuggestedTerm = _PageSearchResult['didYouMean']

        if not _PageSearchResult['results']:
            return

        for _ProductSearchResult in _PageSearchResult['results']:
            if _ProductSearchResult['_type'] == "PRODUCT":
                yield ColesProductOffer.model_validate(_ProductSearchResult)
                _ResultCount += 1

            if _ResultCount == max_results:
                return

        if _Params['page'] == max_page:
            return

        _Params['page'] += 1
