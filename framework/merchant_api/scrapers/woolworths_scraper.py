import urllib.parse

from requests_cache import CachedSession

from framework.merchant_api.domain.scraped_product_offer import WoolworthsProductOffer
from framework.merchant_api.infrastructure.session import create_session


def get_by_stockcode(session: CachedSession, stockcode: str):
    # _Response = session.get(f'https://www.woolworths.com.au/api/v3/ui/schemaorg/product/{stockcode}')

    _Url = 'https://www.woolworths.com.au/apis/ui/Search/products'
    _Body = {
        'Location': f'/shop/search/products?{urllib.parse.urlencode({"searchTerm": stockcode})}',
        'PageNumber': 1,
        'PageSize': 36,
        'SearchTerm': stockcode,
        'SortType': "TraderRelevance"
    }

    _PageSearchResult = session.post(_Url, json=_Body).json()
    return WoolworthsProductOffer.model_construct(**_PageSearchResult['Products'][0]['Products'][0])

def search(session: CachedSession, search_term: str, start_page: int, max_page: int, max_results: int):
    _Url = 'https://www.woolworths.com.au/apis/ui/Search/products'
    _Body = {
        'Filters': [],
        'IsSpecial': False,
        'Location': f'/shop/search/products?{urllib.parse.urlencode({"searchTerm": search_term})}',
        'PageNumber': start_page,
        'PageSize': 36,
        'SearchTerm': search_term,
        'SortType': "TraderRelevance"
    }

    _SuggestedTerm: str = None
    _ResultCount = 0
    while True:
        _PageSearchResult = session.post(_Url, json=_Body).json()
        _SuggestedTerm = _PageSearchResult['SuggestedTerm'] # TOOD: Return out of use case as separate parameter

        if not _PageSearchResult['Products']:
            return

        # TODO: Figure out if validation would be useful
        # Remove '.model_construct' to get validation
        # Could give defaults to get around unwanted validation...
        for _ProductSearchResult in _PageSearchResult['Products']:
            yield WoolworthsProductOffer.model_construct(**_ProductSearchResult['Products'][0])

            _ResultCount += 1
            if _ResultCount == max_results:
                return

        if _Body['PageNumber'] == max_page:
            return

        _Body['PageNumber'] += 1

'''
Notes
    - Call an RPC from web app, under web scraper controller?, or "get products" endpoint? (no should be first option)
        - Searching all merchants or some? which ones? request body options for API?
    - API calls IA controller for scraper
    - Scraper gets results, turning them into product offers (from main domain), by calling main IA controller for create product offer??
        - For current product, try get product offer by id, should it update? should it always create a new offer??

    - Woolies and Coles "products" need to be translated into a single "product", then sent back to web app
    - Linked products will be created and saved through the API with the info provided from the web app (via the scraper)

    - Definitely keep merchants separate, in case one breaks
'''
