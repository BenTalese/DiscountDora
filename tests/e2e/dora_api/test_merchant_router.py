import uuid

import requests

from tests.support import is_valid_uuid

#region ---------------- setup ----------------

# FU-166: list endpoints take query options on the query string and return a
# `{items, total, page, limit}` envelope; query-option errors come back via
# `bad_request(str(exc))` (message in `title`). Seed now has 4 merchants
# (Woolworths, Coles, Aldi, IGA). NB: only the *scraping* surface was removed
# (companion app) — merchants remain first-class entities, so these list tests
# stay; they were just on the stale contract.

base_route = 'http://localhost:5170/api/merchants'

#endregion setup

#region ---------------- get_merchants tests ----------------


def test__get_merchants__GettingMerchant__GetsAllExpectedAttributes(api):
    _Merchant = requests.get(f'{base_route}?filter=name:eq:Woolworths').json()['items'][0]

    assert is_valid_uuid(_Merchant['merchant_id'])
    assert _Merchant['name'] == 'Woolworths'
    assert _Merchant.keys() == {
        'merchant_id',
        'name'
    }


def test__get_merchants__GettingAllMerchants__GetsAllMerchants(api):
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert len(_Response.json()['items']) == 4
    assert _Response.json()['total'] == 4


def test__get_merchants__FilteringByName__GetsSingleMatchingMerchant(api):
    _Response = requests.get(f'{base_route}?filter=name:eq:woolworths')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Woolworths'
    assert len(_Response.json()['items']) == 1


def test__get_merchants__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?filter=thing:eq:woolworths')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "Field 'thing' is not filterable on 'Merchant'.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_merchants__FilteringForMerchantThatDoesNotExist__EmptyResult(api):
    _Response = requests.get(f'{base_route}?filter=merchant_id:eq:{uuid.uuid4()}')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'] == []
    assert _Response.json()['total'] == 0


def test__get_merchants__FilteringWithUnsupportedOperator__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?filter=merchant_id:xx:{uuid.uuid4()}')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "Unsupported filter operator 'xx'. Supported: ct, eq, ge, gt, le, lt, ne.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_merchants__SortingByNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?sort=thing:desc')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'status': 400,
        'errors': {},
        'title': "Field 'thing' is not filterable on 'Merchant'.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_merchants__SortingByNameAscending__MerchantsSortedByNameAscending(api):
    _Items = requests.get(f'{base_route}?sort=name:asc').json()['items']

    assert _Items[0]['name'] == 'Aldi'
    assert _Items[1]['name'] == 'Coles'


def test__get_merchants__SortingByNameDescending__MerchantsSortedByNameDescending(api):
    _Items = requests.get(f'{base_route}?sort=name:desc').json()['items']

    assert _Items[0]['name'] == 'Woolworths'
    assert _Items[1]['name'] == 'IGA'


def test__get_merchants__GettingOneMerchantPerPage__GetsPageOfOneMerchant(api):
    _Response = requests.get(f'{base_route}?sort=name:asc&page=1&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Aldi'
    assert len(_Response.json()['items']) == 1


def test__get_merchants__GettingSecondPage__GetsSecondPageOfMerchants(api):
    _Response = requests.get(f'{base_route}?sort=name:asc&page=2&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Coles'
    assert len(_Response.json()['items']) == 1


def test__get_merchants__PageValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?page=true&limit=2')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'status': 400,
        'errors': {},
        'title': "'page' must be an integer.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_merchants__LimitValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?page=1&limit=true')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'status': 400,
        'errors': {},
        'title': "'limit' must be an integer.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_merchants__PageWithoutLimit__DefaultsLimit(api):
    # FU-166: page/limit are now independently optional (limit defaults to 50).
    _Response = requests.get(f'{base_route}?page=1')

    assert _Response.status_code == 200
    assert _Response.json()['page'] == 1
    assert _Response.json()['limit'] == 50
    assert len(_Response.json()['items']) == 4


def test__get_merchants__LimitWithoutPage__DefaultsPage(api):
    _Response = requests.get(f'{base_route}?limit=1')

    assert _Response.status_code == 200
    assert _Response.json()['page'] == 1
    assert _Response.json()['limit'] == 1
    assert len(_Response.json()['items']) == 1


def test__get_merchants__FilteringSortingAndPagingMerchants__GetsMatchingMerchants(api):
    _Response = requests.get(f'{base_route}?filter=name:ct:wool&sort=name:asc&page=1&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Woolworths'
    assert len(_Response.json()['items']) == 1


#endregion get_merchants tests
