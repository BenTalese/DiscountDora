import uuid
from dataclasses import asdict
from unittest.mock import ANY

import requests

from framework.dora_api.routes.stock_locations.create_stock_location_command import \
    CreateStockLocationCommand
from tests.support import is_valid_uuid

#region ---------------- setup ----------------

base_route = 'http://localhost:5170/api/stock-locations'

#endregion setup

#region ---------------- create_stock_location_async tests ----------------


def test__create_stock_location_async__CreatingStockLocationWithAllAttributes__StockLocationCreated(api):
    _Request = asdict(CreateStockLocationCommand(name = 'Freezer'))

    _Response = requests.post(base_route, json = _Request)

    assert _Response.status_code == 201
    assert _Response.headers['Content-Type'] == 'application/json'
    assert 'http://localhost:5170/api/stock-locations/filter=stock_location_id:eq:' in _Response.headers['location']
    assert _Response.json()['id'] == ANY


def test__create_stock_location_async__StockLocationAlreadyExists__IsBusinessRuleViolation(api):
    _Request = asdict(CreateStockLocationCommand(name = 'frEEzer'))

    _Response = requests.post(base_route, json = _Request)

    assert _Response.status_code == 422
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {
            '': ["A stock location with the name 'frEEzer' already exists."],
        },
       'status': 422,
       'title': 'Business rule violation.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }


def test__create_stock_location_async__EmptyRequest__IsRequiredInputsValidationFailure(api):
    _Response = requests.post(base_route, json = {})

    assert _Response.status_code == 422
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'Required inputs are missing values.',
        'errors': {
            'name': ["'name' must have a value."]
        },
       'status': 422,
       'title': 'Validation failure.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }


#endregion create_stock_location_async tests

#region ---------------- get_stock_locations_async tests ----------------


def test__get_stock_locations_async__GettingStockLocations__GetsAllExpectedAttributes(api):
    _StockLocation = requests.get(base_route).json()[0]

    assert _StockLocation['name'] == 'Pantry'
    assert is_valid_uuid(_StockLocation['stock_location_id'])
    assert _StockLocation.keys() == {
        'name',
        'stock_location_id'
    }


def test__get_stock_locations_async__GettingAllStockLocations__GetsAllStockLocations(api):
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert len(_Response.json()) == 2


def test__get_stock_locations_async__FilteringByName__GetsSingleMatchingStockLocation(api):
    _Response = requests.get(f'{base_route}/filter=name:eq:pantrY')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Pantry'
    assert len(_Response.json()) == 1


def test__get_stock_locations_async__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=poopus_goopus:eq:Pantry')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'Queried attribute(s) do not exist on response: poopus_goopus.',
        'errors': {},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_locations_async__FilteringForStockLocationThatDoesNotExist__EmptyResult(api):
    _Response = requests.get(f'{base_route}/filter=stock_location_id:eq:{uuid.uuid4()}')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == []


def test__get_stock_locations_async__FilteringWithUnsupportedOperator__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=stock_location_id:xx:{uuid.uuid4()}')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': "The filter operator xx is not supported. Supported operators include 'eq', 'lt', 'gt', 'le', 'ge', 'ne' and 'ct'.",
        'errors': {},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_locations_async__SortingByNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/sort=dingo:desc')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "Sort field 'dingo' does not exist in the view model.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_locations_async__SortingByNameAscending__StockLocationsSortedByNameAscending(api):
    _Response = requests.get(f'{base_route}/sort=name:asc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Freezer'
    assert _Response.json()[1]['name'] == 'Pantry'


def test__get_stock_locations_async__SortingByNameDescending__StockLocationsSortedByNameDescending(api):
    _Response = requests.get(f'{base_route}/sort=name:desc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Pantry'
    assert _Response.json()[1]['name'] == 'Freezer'


def test__get_stock_locations_async__GettingOneStockLocationPerPage__GetsPageOfOneStockLocation(api):
    _Response = requests.get(f'{base_route}/page=1&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Pantry'
    assert len(_Response.json()) == 1


def test__get_stock_locations_async__GettingSecondPage__GetsSecondPageOfStockLocations(api):
    _Response = requests.get(f'{base_route}/page=2&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Freezer'
    assert len(_Response.json()) == 1


def test__get_stock_locations_async__PageValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=true&limit=2')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "The page parameter must be an integer.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_locations_async__LimitValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=1&limit=true')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "The limit parameter must be an integer.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_locations_async__PagingWithoutLimit__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "You must use page and limit operations together.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_locations_async__LimitingWithoutPage__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/limit=1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "You must use page and limit operations together.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_locations_async__FilteringSortingAndPagingStockLocations__GetsMatchingStockLocations(api):
    _Response = requests.get(f'{base_route}/filter=name:ct:pan&sort=name:asc&page=1&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Pantry'
    assert len(_Response.json()) == 1


#endregion get_stock_locations_async tests

#region ---------------- update_stock_location_async tests ----------------

#endregion update_stock_location_async tests

#region ---------------- delete_stock_location_async tests ----------------


def test__delete_stock_location_async__DeletingStockLocation__StockLocationDeleted(api):
    _StockLocationID = requests.get(f'{base_route}/filter=name:eq:pantry').json()[0]['stock_location_id']
    _Response = requests.delete(f"{base_route}/{_StockLocationID}")

    assert _Response.status_code == 204
    assert _Response.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert requests.get(f'{base_route}/filter=stock_location_id:eq:{_StockLocationID}').json() == []


def test__delete_stock_location_async__StockLocationDoesNotExist__StockLocationNotFound(api):
    _RandomID = uuid.uuid4()
    _Response = requests.delete(f"{base_route}/{_RandomID}")

    assert _Response.status_code == 404
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": f"StockLocation with the ID '{_RandomID}' was not found.",
        "errors": {},
        "status": 404,
        "title": "Entity was not found.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4"
    }


#endregion delete_stock_location_async tests
