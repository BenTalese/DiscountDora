import uuid
from dataclasses import asdict
from unittest.mock import ANY

import pytest
import requests
from varname import nameof

from framework.dora_api.routes.stock_items.create_stock_item_command import \
    CreateStockItemCommand
from framework.dora_api.routes.stock_items.update_stock_item_command import \
    UpdateStockItemCommand
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


def test__create_stock_item_async__CreatingStockItemWithAllAttributes__StockItemCreated(api, stock_level_id, stock_location_id):
    _StockItemRequest = asdict(CreateStockItemCommand(
        name = 'Peters Neopolitan Ice Cream',
        stock_level_id = stock_level_id,
        stock_location_id = stock_location_id
    ))

    _Response = requests.post(base_route, json = _StockItemRequest)

    assert _Response.status_code == 201
    assert _Response.headers['Content-Type'] == 'application/json'
    assert 'http://localhost:5170/api/stock-items/filter=stock_item_id:eq:' in _Response.headers['location']
    assert _Response.json()['id'] == ANY


def test__create_stock_item_async__CreatingStockItemWithIncorrectDataTypes__CannotBeDeserialised(api):
    _StockItemRequest = asdict(CreateStockItemCommand(
        name = True,
        stock_level_id = 5,
        stock_location_id = "aaa"
    ))

    _Response = requests.post(base_route, json = _StockItemRequest)

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == {
        "errors": {
            "stock_level_id": "Expected type '<class 'uuid.UUID'>'. 'int' object has no attribute 'replace'",
            "stock_location_id": "Expected type '<class 'uuid.UUID'>'. badly formed hexadecimal UUID string"
        },
        "status": 400,
        "title": "Malformed request. One or more request properties could not be deserialised.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__create_stock_item_async__CreatingStockItemWithOnlyRequiredAttributes__StockItemCreated(api, stock_level_id):
    _StockItemRequest = CreateStockItemCommand(
        name = "Freddo Brownie Ice Cream",
        stock_level_id = stock_level_id,
        stock_location_id = None)

    delattr(_StockItemRequest, nameof(_StockItemRequest.stock_location_id))

    _Response = requests.post(base_route, json = _StockItemRequest.__dict__)

    assert _Response.status_code == 201
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['id'] == ANY


def test__create_stock_item_async__StockItemAlreadyExists__IsBusinessRuleViolation(api, stock_level_id, stock_location_id):
    _StockItemRequest = asdict(CreateStockItemCommand(
        name = 'PeTers NeoPOLitan IcE CrEam',
        stock_level_id = stock_level_id,
        stock_location_id = stock_location_id
    ))

    _Response = requests.post(base_route, json = _StockItemRequest)

    assert _Response.status_code == 422
    assert _Response.json() == {
        'errors': {
            'name': ["A stock item with the name 'PeTers NeoPOLitan IcE CrEam' already exists."],
        },
       'status': 422,
       'title': 'Business rule violation.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }


def test__create_stock_item_async__EmptyRequest__IsRequiredInputsValidationFailure(api):
    _Response = requests.post(base_route, json = {})

    assert _Response.status_code == 422
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'errors': {
            'name': ["'name' must have a value."],
            'stock_level_id': ["'stock_level_id' must have a value."]
        },
       'status': 422,
       'title': 'Validation failure.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }


def test__create_stock_item_async__NonExistentEntities__IsEntityExistenceFailure(api):
    _FakeID = str(uuid.uuid4())
    _StockItemRequest = asdict(CreateStockItemCommand(
        name = 'Halo Top Ice Cream',
        stock_level_id = _FakeID,
        stock_location_id = _FakeID
    ))

    _Response = requests.post(base_route, json = _StockItemRequest)

    assert _Response.status_code == 422
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'errors': {
            'stock_level_id': [f"StockLevel with the ID '{_FakeID}' was not found."],
            'stock_location_id': [f"StockLocation with the ID '{_FakeID}' was not found."]
        },
       'status': 422,
       'title': 'Various errors.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }


#endregion create_stock_item_async tests

#region ---------------- get_stock_items_async tests ----------------


def test__get_stock_items_async__GettingStockItem__GetsAllExpectedAttributes(api):
    _StockItem = requests.get(base_route).json()[0]

    assert _StockItem['name'] == 'Kensington Pride Mangoes'
    assert is_valid_uuid(_StockItem['stock_item_id']) is True
    assert is_valid_uuid(_StockItem['stock_level_id']) is True
    assert is_valid_datetime(_StockItem['stock_level_last_updated'], '%a, %d %b %Y %H:%M:%S %Z') is True
    assert is_valid_uuid(_StockItem['stock_location_id']) is True
    assert _StockItem.keys() == {
        'name',
        'stock_item_id',
        'stock_level_id',
        'stock_level_last_updated',
        'stock_location_id'
    }


def test__get_stock_items_async__GettingAllStockItems__GetsAllStockItems(api):
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert len(_Response.json()) == 5


def test__get_stock_items_async__FilteringByName__GetsSingleMatchingStockItem(api):
    _Response = requests.get(f'{base_route}/filter=name:eq:Peters Neopolitan Ice Cream')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Peters Neopolitan Ice Cream'
    assert len(_Response.json()) == 1


def test__get_stock_items_async__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=stock_item_name:eq:Peters Neopolitan Ice Cream')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'errors': {'': 'Queried attribute(s) do not exist on response: stock_item_name.'},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_items_async__FilteringForStockItemThatDoesNotExist__EmptyResult(api):
    _Response = requests.get(f'{base_route}/filter=stock_item_id:eq:{uuid.uuid4()}')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == []


def test__get_stock_items_async__FilteringWithUnsupportedOperator__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=stock_item_id:xx:{uuid.uuid4()}')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'errors': {'': "The filter operator xx is not supported. Supported operators include 'eq', 'lt', 'gt', 'le', 'ge', 'ne' and 'ct'."},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stock_items_async__SortingByNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/sort=stockcode:desc')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': "Sort field 'stockcode' does not exist in the view model."},
        "status": 400,
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_items_async__SortingByNameAscending__StockItemsSortedByNameAscending(api):
    _Response = requests.get(f'{base_route}/sort=name:asc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Freddo Brownie Ice Cream'
    assert _Response.json()[1]['name'] == 'Hot Crispy Chippies'
    assert _Response.json()[2]['name'] == 'Kensington Pride Mangoes'
    assert _Response.json()[3]['name'] == 'Peters Neopolitan Ice Cream'
    assert _Response.json()[4]['name'] == 'Super Awesome Pizza'


def test__get_stock_items_async__SortingByNameDescending__StockItemsSortedByNameDescending(api):
    _Response = requests.get(f'{base_route}/sort=name:desc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Super Awesome Pizza'
    assert _Response.json()[1]['name'] == 'Peters Neopolitan Ice Cream'
    assert _Response.json()[2]['name'] == 'Kensington Pride Mangoes'
    assert _Response.json()[3]['name'] == 'Hot Crispy Chippies'
    assert _Response.json()[4]['name'] == 'Freddo Brownie Ice Cream'


def test__get_stock_items_async__GettingTwoStockItemsPerPage__GetsPageOfTwoStockItems(api):
    _Response = requests.get(f'{base_route}/page=1&limit=2')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Kensington Pride Mangoes'
    assert _Response.json()[1]['name'] == 'Super Awesome Pizza'
    assert len(_Response.json()) == 2


def test__get_stock_items_async__GettingSecondPage__GetsSecondPageOfStockItems(api):
    _Response = requests.get(f'{base_route}/page=2&limit=2')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[1]['name'] == 'Peters Neopolitan Ice Cream'
    assert _Response.json()[0]['name'] == 'Hot Crispy Chippies'
    assert len(_Response.json()) == 2


def test__get_stock_items_async__PageValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=true&limit=2')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': "The page parameter must be an integer."},
        "status": 400,
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_items_async__LimitValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=1&limit=true')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': "The limit parameter must be an integer."},
        "status": 400,
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_items_async__PagingWithoutLimit__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/page=1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': "You must use page and limit operations together."},
        "status": 400,
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_items_async__LimitingWithoutPage__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/limit=1')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': "You must use page and limit operations together."},
        "status": 400,
        "title": "Unsupported query operation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__get_stock_items_async__FilteringSortingAndPagingStockItems__GetsMatchingStockItems(api):
    _Response = requests.get(f'{base_route}/filter=name:ct:iCe CrEam&sort=name:asc&page=2&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Peters Neopolitan Ice Cream'
    assert len(_Response.json()) == 1


#endregion get_stock_items_async tests

#region ---------------- update_stock_item_async tests ----------------


def test__update_stock_item_async__EmptyUpdate__StockItemUnaffected(api):
    _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:hOt_CrIsPy_ChiPPieS').json()[0]
    _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json = {})
    _StockItemAfterPatchOperation = requests.get(f'{base_route}/filter=name:eq:hOt_CrIsPy_ChiPPieS').json()[0]

    assert _PatchResponse.status_code == 204
    assert _PatchResponse.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert _StockItemToUpdate == _StockItemAfterPatchOperation


def test__update_stock_item_async__UpdatingAllAttributes__AllAttributesUpdated(api, stock_level_id, stock_location_id):
    _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:hOt_CrIsPy_ChiPPieS').json()[0]

    _ProductRequest = asdict(UpdateStockItemCommand(
        name = "Old Soggy Chips",
        stock_location_id = stock_location_id,
        stock_level_id = stock_level_id
    ))

    _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json = _ProductRequest)
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


def test__update_stock_item_async__StockItemDoesNotExist__StockItemNotFound(api):
    _RandomID = uuid.uuid4()
    _Response = requests.patch(f"{base_route}/{_RandomID}", json = {})

    assert _Response.status_code == 404
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': f"StockItem with the ID '{_RandomID}' was not found."},
        "status": 404,
        "title": "Entity was not found.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4"
    }


def test__update_stock_item_async__OtherStockItemHasSameName__CannotUpdateToDuplicateName(api):
    _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:kensingTOn_PrIdE_ManGOes').json()[0]
    _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json = {'name': 'super AWESOME pizza'})

    assert _PatchResponse.status_code == 422
    assert _PatchResponse.headers['Content-Type'] == 'application/problem+json'
    assert _PatchResponse.json() == {
        "errors": {
            'name': ["A stock item with the name 'super AWESOME pizza' already exists."]
        },
        "status": 422,
        "title": "Business rule violation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"
    }


#endregion update_stock_item_async tests

#region ---------------- delete_stock_item_async tests ----------------


def test__delete_stock_item_async__DeletingStockItem__StockItemDeleted(api):
    _StockItemID = requests.get(f'{base_route}/filter=name:eq:super AWESOME pizza').json()[0]['stock_item_id']
    _Response = requests.delete(f"{base_route}/{_StockItemID}")

    assert _Response.status_code == 204
    assert _Response.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert requests.get(f'{base_route}/filter=stock_item_id:eq:{_StockItemID}').json() == []


def test__delete_stock_item_async__StockItemDoesNotExist__StockItemNotFound(api):
    _RandomID = uuid.uuid4()
    _Response = requests.delete(f"{base_route}/{_RandomID}")

    assert _Response.status_code == 404
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "errors": {'': f"StockItem with the ID '{_RandomID}' was not found."},
        "status": 404,
        "title": "Entity was not found.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4"
    }


#endregion delete_stock_item_async tests
