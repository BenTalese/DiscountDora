import uuid

import requests

from tests.support import is_valid_uuid

#region ---------------- setup ----------------

base_route = 'http://localhost:5170/api/merchants'

#endregion setup

#region ---------------- get_merchants_async tests ----------------


def test__get_merchants__GettingMerchant__GetsAllExpectedAttributes(api):
    _Merchant = requests.get(base_route).json()[0]

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
    assert len(_Response.json()) == 2


def test__get_merchants__FilteringByName__GetsSingleMatchingMerchant(api):
    _Response = requests.get(f'{base_route}/filter=name:eq:woolworths')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Woolworths'
    assert len(_Response.json()) == 1


def test__get_merchants__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=thing:eq:woolworths')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'Queried attribute(s) do not exist on response: thing.',
        'errors': {},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_merchants__FilteringForMerchantThatDoesNotExist__EmptyResult(api):
    _Response = requests.get(f'{base_route}/filter=merchant_id:eq:{uuid.uuid4()}')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == []


def test__get_merchants__FilteringWithUnsupportedOperator__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=merchant_id:xx:{uuid.uuid4()}')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': "The filter operator 'xx' is not supported. Supported operators: 'eq', 'ne', 'lt', 'gt', 'le', 'ge', 'ct'.",
        'errors': {},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_merchants__SortingByNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/sort=thing:desc')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "Sort field 'thing' does not exist in the view model.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_merchants__SortingByNameAscending__MerchantsSortedByNameAscending(api):
    _Response = requests.get(f'{base_route}/sort=name:asc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Coles'
    assert _Response.json()[1]['name'] == 'Woolworths'


def test__get_merchants__SortingByNameDescending__MerchantsSortedByNameDescending(api):
    _Response = requests.get(f'{base_route}/sort=name:desc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Woolworths'
    assert _Response.json()[1]['name'] == 'Coles'


def test__get_merchants__GettingOneMerchantPerPage__GetsPageOfOneMerchant(api):
    _Response = requests.get(f'{base_route}/page=1&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Woolworths'
    assert len(_Response.json()) == 1


def test__get_merchants__GettingSecondPage__GetsSecondPageOfMerchants(api):
    _Response = requests.get(f'{base_route}/page=2&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Coles'
    assert len(_Response.json()) == 1


def test__get_merchants__PageValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=true&limit=2')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": 'Page and limit must be integers.',
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_merchants__LimitValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=1&limit=true')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": 'Page and limit must be integers.',
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_merchants__PagingWithoutLimit__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": 'You must use page and limit together.',
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_merchants__LimitingWithoutPage__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/limit=1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": 'You must use page and limit together.',
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_merchants__FilteringSortingAndPagingStockItems__GetsMatchingMerchants(api):
    _Response = requests.get(f'{base_route}/filter=name:ct:wool&sort=name:asc&page=1&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Woolworths'
    assert len(_Response.json()) == 1


#endregion get_merchants_async tests
