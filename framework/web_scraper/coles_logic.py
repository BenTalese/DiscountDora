import json

from bs4 import BeautifulSoup
from requests_cache import CachedSession

from framework.web_scraper.models import ColesProductOffer


def search(session: CachedSession, search_term: str, start_page: int = 1, max_page: int = 0):
    _Response = session.get('https://www.coles.com.au/')
    _Soup = BeautifulSoup(_Response.text, features="html.parser")
    _BuildID = json.loads(_Soup.find(id='__NEXT_DATA__').contents[0])['buildId']

    _Url = f'https://www.coles.com.au/_next/data/{_BuildID}/en/search.json'
    _Params = {
        'q': search_term,
        'page': start_page,
    }
    # if specials_only:
    #     params['filter_Special'] = 'all'

    _SuggestedTerm: str = None
    while True:
        _PageSearchResult = session.get(_Url, _Params).json()['pageProps']['searchResults']
        # TODO: Return out of use case as separate parameter
        # TODO: suggested term is a list?
        _SuggestedTerm = _PageSearchResult['didYouMean']

        if not _PageSearchResult['results']:
            break

        for _ProductSearchResult in _PageSearchResult['results']:
            yield ColesProductOffer.model_validate(_ProductSearchResult)

        if _Params['page'] == max_page:
            break

        _Params['page'] += 1