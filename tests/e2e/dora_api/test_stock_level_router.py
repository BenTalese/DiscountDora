import uuid

import requests

from tests.support import is_valid_uuid

#region ---------------- setup ----------------

# the list endpoints now (a) take query options on the query string
# (`?filter=…&sort=…&page=…&limit=…`) rather than as a path segment, and
# (b) return a pagination envelope `{items, total, page, limit}` instead of a
# bare array. Query-option errors are surfaced as `bad_request(str(exc))`, so
# the message lands in `title` (with a generic `detail`). These tests were
# rewritten to that contract.

base_route = 'http://localhost:5170/api/stock-levels'

#endregion setup

#region ---------------- get_stock_levels tests ----------------


def test__get_stock_levels__GettingStockLevel__GetsAllExpectedAttributes(api):
    # Sort explicitly — without a sort clause the envelope order is the DB's
    # natural order, not sequence order.
    _StockLevel = requests.get(f'{base_route}?sort=sequence:asc').json()['items'][0]

    assert _StockLevel['name'] == 'Stocked'
    assert _StockLevel['sequence'] == 0
    assert is_valid_uuid(_StockLevel['stock_level_id'])
    assert _StockLevel.keys() == {
        'name',
        'sequence',
        'stock_level_id'
    }


def test__get_stock_levels__GettingAllStockLevels__GetsAllStockLevels(api):
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert len(_Response.json()['items']) == 3
    assert _Response.json()['total'] == 3


def test__get_stock_levels__FilteringBySequence__GetsSingleMatchingStockLevel(api):
    _Response = requests.get(f'{base_route}?filter=sequence:gt:1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Out of Stock'
    assert len(_Response.json()['items']) == 1


def test__get_stock_levels__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?filter=thing:eq:1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "Field 'thing' is not filterable on 'StockLevel'.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_levels__FilteringForStockLevelThatDoesNotExist__EmptyResult(api):
    _Response = requests.get(f'{base_route}?filter=stock_level_id:eq:{uuid.uuid4()}')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'] == []
    assert _Response.json()['total'] == 0


def test__get_stock_levels__FilteringWithUnsupportedOperator__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?filter=stock_level_id:xx:{uuid.uuid4()}')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "Unsupported filter operator 'xx'. Supported: ct, eq, ge, gt, le, lt, ne.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_levels__SortingByNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?sort=thing:desc')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "Field 'thing' is not filterable on 'StockLevel'.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_levels__SortingBySequenceAscending__StockLevelsSortedBySequenceAscending(api):
    _Items = requests.get(f'{base_route}?sort=sequence:asc').json()['items']

    assert _Items[0]['name'] == 'Stocked'
    assert _Items[1]['name'] == 'Low Stock'
    assert _Items[2]['name'] == 'Out of Stock'


def test__get_stock_levels__SortingBySequenceDescending__StockLevelsSortedBySequenceDescending(api):
    _Items = requests.get(f'{base_route}?sort=sequence:desc').json()['items']

    assert _Items[0]['name'] == 'Out of Stock'
    assert _Items[1]['name'] == 'Low Stock'
    assert _Items[2]['name'] == 'Stocked'


def test__get_stock_levels__GettingTwoStockLevelsPerPage__GetsPageOfTwoStockLevels(api):
    _Response = requests.get(f'{base_route}?sort=sequence:asc&page=1&limit=2')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Stocked'
    assert _Response.json()['items'][1]['name'] == 'Low Stock'
    assert len(_Response.json()['items']) == 2
    assert _Response.json()['total'] == 3


def test__get_stock_levels__GettingSecondPage__GetsSecondPageOfStockLevels(api):
    _Response = requests.get(f'{base_route}?sort=sequence:asc&page=2&limit=2')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Out of Stock'
    assert len(_Response.json()['items']) == 1


def test__get_stock_levels__PageValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?page=true&limit=2')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "'page' must be an integer.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_levels__LimitValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?page=1&limit=true')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "'limit' must be an integer.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_levels__PageWithoutLimit__DefaultsLimit(api):
    # the old "you must use page and limit together" rule was removed —
    # `page` and `limit` are now independently optional (limit defaults to 50).
    _Response = requests.get(f'{base_route}?page=1')

    assert _Response.status_code == 200
    assert _Response.json()['page'] == 1
    assert _Response.json()['limit'] == 50
    assert len(_Response.json()['items']) == 3


def test__get_stock_levels__LimitWithoutPage__DefaultsPage(api):
    # limit alone is now valid; page defaults to 1.
    _Response = requests.get(f'{base_route}?limit=1')

    assert _Response.status_code == 200
    assert _Response.json()['page'] == 1
    assert _Response.json()['limit'] == 1
    assert len(_Response.json()['items']) == 1


def test__get_stock_levels__FilteringSortingAndPagingStockLevels__GetsMatchingStockLevels(api):
    _Response = requests.get(f'{base_route}?filter=sequence:gt:0&sort=sequence:desc&page=2&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    # sequence>0 → Low(1), Out(2); desc → Out, Low; page 2 of 2 → Low Stock.
    assert _Response.json()['items'][0]['name'] == 'Low Stock'
    assert len(_Response.json()['items']) == 1
    assert _Response.json()['total'] == 2


#endregion get_stock_levels tests
