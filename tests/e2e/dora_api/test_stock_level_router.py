import uuid

import requests

from tests.support import is_valid_uuid

#region ---------------- setup ----------------

base_route = 'http://localhost:5170/api/stock-levels'

#endregion setup

#region ---------------- get_stock_levels_async tests ----------------


def test__get_stock_levels_async__GettingStockLevel__GetsAllExpectedAttributes(api):
    _StockLevel = requests.get(base_route).json()[0]

    assert _StockLevel['name'] == 'Well-Stocked'
    assert _StockLevel['sequence'] == 0
    assert is_valid_uuid(_StockLevel['stock_level_id'])
    assert _StockLevel.keys() == {
        'name',
        'sequence',
        'stock_level_id'
    }


def test__get_stock_levels_async__GettingAllStockLevels__GetsAllStockLevels(api):
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert len(_Response.json()) == 4


def test__get_stock_levels_async__FilteringBySequence__GetsSingleMatchingStockLevel(api):
    _Response = requests.get(f'{base_route}/filter=sequence:gt:2')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Out of Stock'
    assert len(_Response.json()) == 1


def test__get_stock_levels_async__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=thing:eq:1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'errors': {'': 'Queried attribute(s) do not exist on response: thing.'},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_levels_async__FilteringForStockLevelThatDoesNotExist__EmptyResult(api):
    _Response = requests.get(f'{base_route}/filter=stock_level_id:eq:{uuid.uuid4()}')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == []


def test__get_stock_levels_async__FilteringWithUnsupportedOperator__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=stock_level_id:xx:{uuid.uuid4()}')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'errors': {'': "The filter operator xx is not supported. Supported operators include 'eq', 'lt', 'gt', 'le', 'ge', 'ne' and 'ct'."},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_levels_async__SortingByNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/sort=thing:desc')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': "Sort field 'thing' does not exist in the view model."},
        "status": 400,
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_levels_async__SortingBySequenceAscending__StockLevelsSortedBySequenceAscending(api):
    _Response = requests.get(f'{base_route}/sort=sequence:asc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Well-Stocked'
    assert _Response.json()[1]['name'] == 'Sufficient Stock'
    assert _Response.json()[2]['name'] == 'Low Stock'
    assert _Response.json()[3]['name'] == 'Out of Stock'


def test__get_stock_levels_async__SortingBySequenceDescending__StockLevelsSortedBySequenceDescending(api):
    _Response = requests.get(f'{base_route}/sort=sequence:desc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Out of Stock'
    assert _Response.json()[1]['name'] == 'Low Stock'
    assert _Response.json()[2]['name'] == 'Sufficient Stock'
    assert _Response.json()[3]['name'] == 'Well-Stocked'


def test__get_stock_levels_async__GettingTwoStockLevelsPerPage__GetsPageOfTwoStockLevels(api):
    _Response = requests.get(f'{base_route}/page=1&limit=2')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Well-Stocked'
    assert _Response.json()[1]['name'] == 'Sufficient Stock'
    assert len(_Response.json()) == 2


def test__get_stock_levels_async__GettingSecondPage__GetsSecondPageOfStockLevels(api):
    _Response = requests.get(f'{base_route}/page=2&limit=2')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Low Stock'
    assert _Response.json()[1]['name'] == 'Out of Stock'
    assert len(_Response.json()) == 2


def test__get_stock_levels_async__PageValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=true&limit=2')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': "The page parameter must be an integer."},
        "status": 400,
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_levels_async__LimitValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=1&limit=true')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': "The limit parameter must be an integer."},
        "status": 400,
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_levels_async__PagingWithoutLimit__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': "You must use page and limit operations together."},
        "status": 400,
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_levels_async__LimitingWithoutPage__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/limit=1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': "You must use page and limit operations together."},
        "status": 400,
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_levels_async__FilteringSortingAndPagingStockItems__GetsMatchingStockLevels(api):
    _Response = requests.get(f'{base_route}/filter=sequence:gt:0&sort=sequence:desc&page=2&limit=2')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Sufficient Stock'
    assert len(_Response.json()) == 1


#endregion get_stock_levels_async tests
