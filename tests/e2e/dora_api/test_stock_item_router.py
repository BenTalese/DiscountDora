import uuid
from dataclasses import asdict
from unittest.mock import ANY

import pytest
import requests
from varname import nameof

from framework.dora_api.routes.stock_items.create_stock_item_command import \
    CreateStockItemCommand

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
        "detail": "See errors property for more details.",
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
        name = "Freddo Brownies",
        stock_level_id = stock_level_id,
        stock_location_id = None)

    delattr(_StockItemRequest, nameof(_StockItemRequest.stock_location_id))

    _Response = requests.post(base_route, json = _StockItemRequest.__dict__)

    assert _Response.status_code == 201
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['id'] == ANY


def test__create_stock_item_async__StockItemAlreadyExists__IsBusinessRuleViolation(api, stock_level_id, stock_location_id):
    _StockItemRequest = asdict(CreateStockItemCommand(
        name = 'Peters Neopolitan Ice Cream',
        stock_level_id = stock_level_id,
        stock_location_id = stock_location_id
    ))

    _Response = requests.post(base_route, json = _StockItemRequest)

    assert _Response.status_code == 422
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {
            '': ["A stock item with the name 'Peters Neopolitan Ice Cream' already exists."],
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
        'detail': 'Required inputs are missing values.',
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
        'detail': 'See errors property for more details.',
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

#endregion get_stock_items_async tests

#region ---------------- update_stock_item_async tests ----------------

#endregion update_stock_item_async tests

#region ---------------- delete_stock_item_async tests ----------------

#endregion delete_stock_item_async tests
