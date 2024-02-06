from typing import Any, Generator

from requests_cache import CachedSession

from framework.merchant_api.domain.entities.iga_product_offer import \
    IgaProductOffer


def get_by_stockcode(session: CachedSession, store_id: int, stockcode: str):
    _Url = f"https://www.igashop.com.au/api/storefront/stores/{store_id}/products/{stockcode}"
    _Response = session.get(_Url)
    return IgaProductOffer.model_validate(_Response.json())


def search(
        session: CachedSession,
        store_id: int,
        search_term: str,
        start_page: int,
        max_page: int,
        max_results: int) -> Generator[IgaProductOffer, Any, None]:

    _Url = f'https://www.igashop.com.au/api/storefront/stores/{store_id}/search'
    _Params = {
        'q': search_term[:50], # no results if query > 50
        'skip': 0,
        'take': max_results
    }

    _ResultCount = 0
    _PageCount = 0
    while True:
        _PageSearchResult = session.get(_Url, _Params).json()

        if not _PageSearchResult['items']:
            break

        for _ProductSearchResult in _PageSearchResult['items']:
            yield IgaProductOffer.model_validate(_ProductSearchResult)
            _ResultCount += 1

            if _ResultCount == max_results:
                return

        if _PageCount == max_page:
            return

        _Params['skip'] += _Params['take']
        _PageCount += 1
