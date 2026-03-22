from uuid import uuid4
from unittest.mock import ANY

import pytest
import requests

from dora_api.features.stock_items.create_stock_item import \
    CreateStockItemRequest
from dora_api.features.stock_items.update_stock_item import \
    UpdateStockItemRequest
from tests.support import is_valid_datetime, is_valid_uuid

#region ---------------- setup ----------------

base_route = 'http://localhost:5170/api/stock-items'


@pytest.fixture
def stock_level_id():
    return requests.get('http://localhost:5170/api/stock-levels').json()[0]['stock_level_id']


@pytest.fixture
def stock_location_id():
    return requests.get('http://localhost:5170/api/stock-locations').json()[0]['stock_location_id']

#endregion setup

#region ---------------- create_stock_item_async tests ----------------


def test__create_stock_item__CreatingStockItemWithAllAttributes__StockItemCreated(api, stock_level_id, stock_location_id):
    _StockItemRequest = CreateStockItemRequest(
        name = 'Peters Neopolitan Ice Cream',
        stock_level_id = stock_level_id,
        stock_location_id = stock_location_id
    )

    _Response = requests.post(base_route, json = _StockItemRequest.model_dump(mode="json"))

    assert _Response.status_code == 201
    assert _Response.headers['Content-Type'] == 'application/json'
    assert 'http://localhost:5170/api/stock-items/filter=stock_item_id:eq:' in _Response.headers['location']
    assert _Response.json()['id'] == ANY


def test__create_stock_item__CreatingStockItemWithIncorrectDataTypes__CannotBeDeserialised(api):
    _Request = {
        "name": True,
        "stock_level_id": 5,
        "stock_location_id": "aaa"
    }

    _Response = requests.post(base_route, json = _Request)
    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "See errors property for more details.",
        "errors": {
            "name": ["Input should be a valid string"],
            "stock_level_id": ["UUID input should be a string, bytes or UUID object"],
            "stock_location_id": ["Input should be a valid UUID, invalid length: expected length 32 for simple format, found 3"]
        },
        "status": 400,
        "title": "Malformed request.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__create_stock_item__CreatingStockItemWithOnlyRequiredAttributes__StockItemCreated(api, stock_level_id):
    _StockItemRequest = CreateStockItemRequest(
        name = "Freddo Brownie Ice Cream",
        stock_level_id = stock_level_id
    )

    _Response = requests.post(base_route, json = _StockItemRequest.model_dump(mode='json'))

    assert _Response.status_code == 201
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['id'] == ANY


def test__create_stock_item__StockItemAlreadyExists__IsBusinessRuleViolation(api, stock_level_id, stock_location_id):
    _StockItemRequest = CreateStockItemRequest(
        name = 'PeTers NeoPOLitan IcE CrEam',
        stock_level_id = stock_level_id,
        stock_location_id = stock_location_id
    )

    _Response = requests.post(base_route, json = _StockItemRequest.model_dump(mode='json'))

    assert _Response.status_code == 422
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {
            '': ["A stock item with the name 'PeTers NeoPOLitan IcE CrEam' already exists."],
        },
       'status': 422,
       'title': 'Business rule violation.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }


def test__create_stock_item__EmptyRequest__IsRequiredInputsValidationFailure(api):
    _Response = requests.post(base_route, json = {})

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {
            'name': ["Field required"],
            'stock_level_id': ["Field required"]
        },
       'status': 400,
       'title': 'Malformed request.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__create_stock_item__StockLevelDoesNotExist__IsEntityExistenceFailure(api):
    _FakeID = uuid4()
    _StockItemRequest = CreateStockItemRequest(
        name = 'Halo Top Ice Cream',
        stock_level_id = _FakeID
    )

    _Response = requests.post(base_route, json = _StockItemRequest.model_dump(mode='json'))

    assert _Response.status_code == 422
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {
            'stock_level_id': [f"StockLevel with the ID '{_FakeID}' was not found."]
        },
       'status': 422,
       'title': 'Entity was not found.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }


def test__create_stock_item__StockLocationDoesNotExist__IsEntityExistenceFailure(api, stock_level_id):
    _FakeID = uuid4()
    _StockItemRequest = CreateStockItemRequest(
        name = 'Halo Top Ice Cream',
        stock_level_id = stock_level_id,
        stock_location_id = _FakeID
    )

    _Response = requests.post(base_route, json = _StockItemRequest.model_dump(mode='json'))

    assert _Response.status_code == 422
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {
            'stock_location_id': [f"StockLocation with the ID '{_FakeID}' was not found."]
        },
       'status': 422,
       'title': 'Entity was not found.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }


#endregion create_stock_item_async tests

#region ---------------- get_stock_items_async tests ----------------


def test__get_stock_items__GettingStockItem__GetsAllExpectedAttributes(api):
    _StockItem = requests.get(base_route).json()[0]

    assert _StockItem['name'] == 'Brazil Nuts'
    assert is_valid_uuid(_StockItem['stock_item_id']) is True
    assert is_valid_uuid(_StockItem['stock_level_id']) is True
    assert is_valid_datetime(_StockItem['stock_level_last_updated'], '%a, %d %b %Y %H:%M:%S %Z') is True
    # assert is_valid_uuid(_StockItem['stock_location_id']) is True
    assert _StockItem.keys() == {
        'name',
        'stock_item_id',
        'stock_level_id',
        'stock_level_last_updated',
        'stock_location_id'
    }


def test__get_stock_items__GettingAllStockItems__GetsAllStockItems(api):
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert len(_Response.json()) == 8


def test__get_stock_items__FilteringByName__GetsSingleMatchingStockItem(api):
    _Response = requests.get(f'{base_route}/filter=name:eq:Peters Neopolitan Ice Cream')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Peters Neopolitan Ice Cream'
    assert len(_Response.json()) == 1


def test__get_stock_items__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=stock_item_name:eq:Peters Neopolitan Ice Cream')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'Queried attribute(s) do not exist on response: stock_item_name.',
        'errors': {},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_items__FilteringForStockItemThatDoesNotExist__EmptyResult(api):
    _Response = requests.get(f'{base_route}/filter=stock_item_id:eq:{uuid4()}')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == []


def test__get_stock_items__FilteringWithUnsupportedOperator__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=stock_item_id:xx:{uuid4()}')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': "The filter operator 'xx' is not supported. Supported operators: 'eq', 'ne', 'lt', 'gt', 'le', 'ge', 'ct'.",
        'errors': {},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_items__SortingByNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/sort=stockcode:desc')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "Sort field 'stockcode' does not exist in the view model.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_items__SortingByNameAscending__StockItemsSortedByNameAscending(api):
    _Response = requests.get(f'{base_route}/sort=name:asc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Barilla Pasta'
    assert _Response.json()[1]['name'] == 'Brazil Nuts'
    assert _Response.json()[2]['name'] == 'Freddo Brownie Ice Cream'
    assert _Response.json()[3]['name'] == 'Hot Crispy Chippies'
    assert _Response.json()[4]['name'] == 'Kensington Pride Mangoes'
    assert _Response.json()[5]['name'] == 'Peters Neopolitan Ice Cream'
    assert _Response.json()[6]['name'] == 'Super Awesome Pizza'
    assert _Response.json()[7]['name'] == 'Vanilla Ice Cream'


def test__get_stock_items__SortingByNameDescending__StockItemsSortedByNameDescending(api):
    _Response = requests.get(f'{base_route}/sort=name:desc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Vanilla Ice Cream'
    assert _Response.json()[1]['name'] == 'Super Awesome Pizza'
    assert _Response.json()[2]['name'] == 'Peters Neopolitan Ice Cream'
    assert _Response.json()[3]['name'] == 'Kensington Pride Mangoes'
    assert _Response.json()[4]['name'] == 'Hot Crispy Chippies'
    assert _Response.json()[5]['name'] == 'Freddo Brownie Ice Cream'
    assert _Response.json()[6]['name'] == 'Brazil Nuts'
    assert _Response.json()[7]['name'] == 'Barilla Pasta'


def test__get_stock_items__GettingTwoStockItemsPerPage__GetsPageOfTwoStockItems(api):
    _Response = requests.get(f'{base_route}/page=1&limit=2')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Brazil Nuts'
    assert _Response.json()[1]['name'] == 'Kensington Pride Mangoes'
    assert len(_Response.json()) == 2


def test__get_stock_items__GettingSecondPage__GetsSecondPageOfStockItems(api):
    _Response = requests.get(f'{base_route}/page=2&limit=2')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[1]['name'] == 'Super Awesome Pizza'
    assert _Response.json()[0]['name'] == 'Barilla Pasta'
    assert len(_Response.json()) == 2


def test__get_stock_items__PageValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=true&limit=2')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "Page and limit must be integers.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_items__LimitValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=1&limit=true')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "Page and limit must be integers.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_items__PagingWithoutLimit__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "You must use page and limit together.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_items__LimitingWithoutPage__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/limit=1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "You must use page and limit together.",
        "status": 400,
        "errors": {},
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_items__FilteringSortingAndPagingStockItems__GetsMatchingStockItems(api):
    _Response = requests.get(f'{base_route}/filter=name:ct:iCe CrEam&sort=name:asc&page=2&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Peters Neopolitan Ice Cream'
    assert len(_Response.json()) == 1


#endregion get_stock_items_async tests

#region ---------------- update_stock_item_async tests ----------------


def test__update_stock_item__EmptyUpdate__StockItemUnaffected(api):
    _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:hOt_CrIsPy_ChiPPieS').json()[0]
    _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json = {})
    _StockItemAfterPatchOperation = requests.get(f'{base_route}/filter=name:eq:hOt_CrIsPy_ChiPPieS').json()[0]

    assert _PatchResponse.status_code == 204
    assert _PatchResponse.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert _StockItemToUpdate == _StockItemAfterPatchOperation


def test__update_stock_item__UpdatingAllAttributes__AllAttributesUpdated(api, stock_level_id, stock_location_id):
    _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:hOt_CrIsPy_ChiPPieS').json()[0]

    _StockItemRequest = UpdateStockItemRequest(
        name = "Old Soggy Chips",
        stock_level_id = stock_level_id,
        stock_location_id = stock_location_id
    ).model_dump(mode = "json")

    _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json = _StockItemRequest)
    _StockItemAfterPatchOperation = requests.get(f'{base_route}/filter=stock_item_id:eq:{_StockItemToUpdate["stock_item_id"]}').json()[0]

    assert _PatchResponse.status_code == 204
    assert _PatchResponse.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert _StockItemToUpdate == {
        'name': 'Hot Crispy Chippies',
        'stock_item_id': _StockItemToUpdate['stock_item_id'],
        'stock_level_id': _StockItemToUpdate['stock_level_id'],
        'stock_level_last_updated': _StockItemToUpdate['stock_level_last_updated'],
        'stock_location_id': _StockItemToUpdate['stock_location_id']
    }
    assert _StockItemAfterPatchOperation == {
        'name': 'Old Soggy Chips',
        'stock_item_id': _StockItemToUpdate['stock_item_id'],
        'stock_level_id': stock_level_id,
        'stock_level_last_updated': ANY,
        'stock_location_id': stock_location_id
    }
    assert _StockItemToUpdate['stock_level_last_updated'] != _StockItemAfterPatchOperation['stock_level_last_updated']


def test__update_stock_item__StockItemDoesNotExist__StockItemNotFound(api):
    _RandomID = uuid4()
    _Response = requests.patch(f"{base_route}/{_RandomID}", json = {})

    assert _Response.status_code == 404
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": f"StockItem with the ID '{_RandomID}' was not found.",
        "errors": {},
        "status": 404,
        "title": "Entity was not found.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4"
    }


def test__update_stock_item__OtherStockItemHasSameName__CannotUpdateToDuplicateName(api):
    _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:kensingTOn_PrIdE_ManGOes').json()[0]

    _StockItemRequest = UpdateStockItemRequest(name = 'super AWESOME pizza').model_dump(exclude_unset=True)

    _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json = _StockItemRequest)

    assert _PatchResponse.status_code == 422
    assert _PatchResponse.headers['Content-Type'] == 'application/problem+json'
    assert _PatchResponse.json() == {
        "detail": "See errors property for more details.",
        "errors": {
            '': ["A stock item with the name 'super AWESOME pizza' already exists."]
        },
        "status": 422,
        "title": "Business rule violation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"
    }


#endregion update_stock_item_async tests

#region ---------------- delete_stock_item_async tests ----------------


def test__delete_stock_item__DeletingStockItem__StockItemDeleted(api):
    _StockItemID = requests.get(f'{base_route}/filter=name:eq:super AWESOME pizza').json()[0]['stock_item_id']
    _Response = requests.delete(f"{base_route}/{_StockItemID}")

    assert _Response.status_code == 204
    assert _Response.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert requests.get(f'{base_route}/filter=stock_item_id:eq:{_StockItemID}').json() == []


def test__delete_stock_item__StockItemDoesNotExist__StockItemNotFound(api):
    _RandomID = uuid4()
    _Response = requests.delete(f"{base_route}/{_RandomID}")

    assert _Response.status_code == 404
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": f"StockItem with the ID '{_RandomID}' was not found.",
        "errors": {},
        "status": 404,
        "title": "Entity was not found.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4"
    }


#endregion delete_stock_item_async tests
