from unittest.mock import ANY
from uuid import uuid4

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

#region ---------------- create_stock_item tests ----------------


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


def test__create_stock_item__EmptyName__IsBadRequest(api, stock_level_id):
    _Request = {
        "name": "",
        "stock_level_id": str(stock_level_id)
    }

    _Response = requests.post(base_route, json=_Request)

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert 'name' in _Response.json()['errors']


def test__create_stock_item__ExtraAttributes__IsBadRequest(api, stock_level_id):
    _Request = {
        "name": "Some Stock Item",
        "stock_level_id": str(stock_level_id),
        "poopusgoopus": "aaaa"
    }

    _Response = requests.post(base_route, json=_Request)

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "See errors property for more details.",
        "errors": {
            "poopusgoopus": ["Extra inputs are not permitted"]
        },
        "status": 400,
        "title": "Malformed request.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__create_stock_item__NullStockLocationId__StockItemCreatedWithNoLocation(api, stock_level_id):
    _StockItemRequest = CreateStockItemRequest(
        name="Null Location Stock Item",
        stock_level_id=stock_level_id,
        stock_location_id=None
    )

    _Response = requests.post(base_route, json=_StockItemRequest.model_dump(mode="json"))

    assert _Response.status_code == 201
    _CreatedItem = requests.get(f'{base_route}/filter=name:eq:Null_Location_Stock_Item').json()[0]
    assert _CreatedItem['stock_location_id'] is None


#endregion create_stock_item tests

#region ---------------- get_stock_items tests ----------------


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
        'stock_location_id',
        'expiry_date',
        'is_flagged'
    }


def test__get_stock_items__GettingAllStockItems__GetsAllStockItems(api):
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert len(_Response.json()) == 9


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
    assert _Response.json()[5]['name'] == 'Null Location Stock Item'
    assert _Response.json()[6]['name'] == 'Peters Neopolitan Ice Cream'
    assert _Response.json()[7]['name'] == 'Super Awesome Pizza'
    assert _Response.json()[8]['name'] == 'Vanilla Ice Cream'


def test__get_stock_items__SortingByNameDescending__StockItemsSortedByNameDescending(api):
    _Response = requests.get(f'{base_route}/sort=name:desc')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['name'] == 'Vanilla Ice Cream'
    assert _Response.json()[1]['name'] == 'Super Awesome Pizza'
    assert _Response.json()[2]['name'] == 'Peters Neopolitan Ice Cream'
    assert _Response.json()[3]['name'] == 'Null Location Stock Item'
    assert _Response.json()[4]['name'] == 'Kensington Pride Mangoes'
    assert _Response.json()[5]['name'] == 'Hot Crispy Chippies'
    assert _Response.json()[6]['name'] == 'Freddo Brownie Ice Cream'
    assert _Response.json()[7]['name'] == 'Brazil Nuts'
    assert _Response.json()[8]['name'] == 'Barilla Pasta'


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


#endregion get_stock_items tests

#region ---------------- update_stock_item tests ----------------


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


def test__update_stock_item__UpdatingNameOnly__OnlyNameChanges(api, stock_level_id):
    _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:kensingTOn_PrIdE_ManGOes').json()[0]
    _OriginalStockLevelId = _StockItemToUpdate['stock_level_id']
    _OriginalStockLevelLastUpdated = _StockItemToUpdate['stock_level_last_updated']

    _PatchRequest = UpdateStockItemRequest(name="Kensington Pride Mangoes Renamed").model_dump(exclude_unset=True)
    _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json=_PatchRequest)
    _StockItemAfterPatch = requests.get(f'{base_route}/filter=stock_item_id:eq:{_StockItemToUpdate["stock_item_id"]}').json()[0]

    assert _PatchResponse.status_code == 204
    assert _StockItemAfterPatch['name'] == 'Kensington Pride Mangoes Renamed'
    assert _StockItemAfterPatch['stock_level_id'] == _OriginalStockLevelId
    assert _StockItemAfterPatch['stock_level_last_updated'] == _OriginalStockLevelLastUpdated


def test__update_stock_item__UpdatingStockLevelOnly__StockLevelLastUpdatedChanges(api, stock_level_id):
    _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:Brazil_Nuts').json()[0]
    _OriginalStockLevelLastUpdated = _StockItemToUpdate['stock_level_last_updated']

    _PatchRequest = UpdateStockItemRequest(stock_level_id=stock_level_id).model_dump(mode="json", exclude_unset=True)
    _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json=_PatchRequest)
    _StockItemAfterPatch = requests.get(f'{base_route}/filter=stock_item_id:eq:{_StockItemToUpdate["stock_item_id"]}').json()[0]

    assert _PatchResponse.status_code == 204
    assert _StockItemAfterPatch['stock_level_id'] == str(stock_level_id)
    assert _StockItemAfterPatch['stock_level_last_updated'] != _OriginalStockLevelLastUpdated
    assert _StockItemAfterPatch['name'] == _StockItemToUpdate['name']


# TODO: Tests aren't working
# def test__update_stock_item__UpdatingStockLocationToNull__StockLocationCleared(api):
#     _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:Brazil_Nuts').json()[0]

#     _PatchRequest = UpdateStockItemRequest(stock_location_id=None).model_dump(mode="json", exclude_unset=True)
#     _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json=_PatchRequest)
#     _StockItemAfterPatch = requests.get(f'{base_route}/filter=stock_item_id:eq:{_StockItemToUpdate["stock_item_id"]}').json()[0]

#     assert _PatchResponse.status_code == 204
#     assert _StockItemAfterPatch['stock_location_id'] is None
#     assert _StockItemAfterPatch['name'] == _StockItemToUpdate['name']


# def test__update_stock_item__UpdatingStockLevelToNonExistentId__IsEntityExistenceFailure(api):
#     _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:Brazil_Nuts').json()[0]
#     _FakeStockLevelId = uuid4()

#     _PatchRequest = UpdateStockItemRequest(stock_level_id=_FakeStockLevelId).model_dump(mode="json", exclude_unset=True)
#     _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json=_PatchRequest)

#     assert _PatchResponse.status_code == 422
#     assert _PatchResponse.headers['Content-Type'] == 'application/problem+json'
#     assert _PatchResponse.json() == {
#         "detail": "See errors property for more details.",
#         "errors": {
#             "stock_level_id": [f"StockLevel with the ID '{_FakeStockLevelId}' was not found."]
#         },
#         "status": 422,
#         "title": "Entity was not found.",
#         "type": "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"
#     }


# def test__update_stock_item__UpdatingStockLocationToNonExistentId__IsEntityExistenceFailure(api):
#     _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:Brazil_Nuts').json()[0]
#     _FakeStockLocationId = uuid4()

#     _PatchRequest = UpdateStockItemRequest(stock_location_id=_FakeStockLocationId).model_dump(mode="json", exclude_unset=True)
#     _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json=_PatchRequest)

#     assert _PatchResponse.status_code == 422
#     assert _PatchResponse.headers['Content-Type'] == 'application/problem+json'
#     assert _PatchResponse.json() == {
#         "detail": "See errors property for more details.",
#         "errors": {
#             "stock_location_id": [f"StockLocation with the ID '{_FakeStockLocationId}' was not found."]
#         },
#         "status": 422,
#         "title": "Entity was not found.",
#         "type": "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"
#     }


# def test__update_stock_item__UpdatingNameToSameNameOnSameItem__IsAllowed(api):
#     """Updating an item's name to its own current name should not trigger the duplicate check."""
#     _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:Brazil_Nuts').json()[0]

#     _PatchRequest = UpdateStockItemRequest(name="Brazil Nuts").model_dump(exclude_unset=True)
#     _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json=_PatchRequest)

#     assert _PatchResponse.status_code == 204


# def test__update_stock_item__IncorrectDataTypes__IsBadRequest(api):
#     _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:Brazil_Nuts').json()[0]

#     _PatchRequest = {
#         "name": True,
#         "stock_level_id": 5,
#         "stock_location_id": "aaa"
#     }
#     _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json=_PatchRequest)

#     assert _PatchResponse.status_code == 400
#     assert _PatchResponse.headers['Content-Type'] == 'application/problem+json'
#     assert _PatchResponse.json() == {
#         "detail": "See errors property for more details.",
#         "errors": {
#             "name": ["Input should be a valid string"],
#             "stock_level_id": ["UUID input should be a string, bytes or UUID object"],
#             "stock_location_id": ["Input should be a valid UUID, invalid length: expected length 32 for simple format, found 3"]
#         },
#         "status": 400,
#         "title": "Malformed request.",
#         "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
#     }


def test__update_stock_item__EmptyName__IsBadRequest(api):
    _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:Brazil_Nuts').json()[0]

    _PatchRequest = {"name": ""}
    _PatchResponse = requests.patch(f"{base_route}/{_StockItemToUpdate['stock_item_id']}", json=_PatchRequest)

    assert _PatchResponse.status_code == 400
    assert _PatchResponse.headers['Content-Type'] == 'application/problem+json'
    assert 'name' in _PatchResponse.json()['errors']


def test__update_stock_item__ExtraAttributes__IsBadRequest(api):
    _StockItemToUpdate = requests.get(f'{base_route}/filter=name:eq:Brazil_Nuts').json()[0]

    _PatchResponse = requests.patch(
        f"{base_route}/{_StockItemToUpdate['stock_item_id']}",
        json={"name": "Brazil Nuts", "poopusgoopus": "aaaa"}
    )

    assert _PatchResponse.status_code == 400
    assert _PatchResponse.headers['Content-Type'] == 'application/problem+json'
    assert _PatchResponse.json() == {
        "detail": "See errors property for more details.",
        "errors": {
            "poopusgoopus": ["Extra inputs are not permitted"]
        },
        "status": 400,
        "title": "Malformed request.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


#endregion update_stock_item tests

#region ---------------- delete_stock_item tests ----------------


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


def test__delete_stock_item__DeletingAlreadyDeletedStockItem__StockItemNotFound(api):
    """Deleting the same item twice should return 404 on the second attempt."""
    _StockItemRequest = CreateStockItemRequest(
        name="Item To Delete Twice",
        stock_level_id=requests.get('http://localhost:5170/api/stock-levels').json()[0]['stock_level_id']
    )
    _CreateResponse = requests.post(base_route, json=_StockItemRequest.model_dump(mode="json"))
    _StockItemId = _CreateResponse.json()['id']

    requests.delete(f"{base_route}/{_StockItemId}")
    _SecondDeleteResponse = requests.delete(f"{base_route}/{_StockItemId}")

    assert _SecondDeleteResponse.status_code == 404
    assert _SecondDeleteResponse.headers['Content-Type'] == 'application/problem+json'
    assert _SecondDeleteResponse.json() == {
        "detail": f"StockItem with the ID '{_StockItemId}' was not found.",
        "errors": {},
        "status": 404,
        "title": "Entity was not found.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4"
    }


def test__delete_stock_item__DeletedItemNoLongerReturnedInGetAll(api):
    _StockItemRequest = CreateStockItemRequest(
        name="Item To Verify Gone",
        stock_level_id=requests.get('http://localhost:5170/api/stock-levels').json()[0]['stock_level_id']
    )
    requests.post(base_route, json=_StockItemRequest.model_dump(mode="json"))
    _StockItemId = requests.get(f'{base_route}/filter=name:eq:Item_To_Verify_Gone').json()[0]['stock_item_id']

    requests.delete(f"{base_route}/{_StockItemId}")
    _GetResponse = requests.get(f'{base_route}/filter=stock_item_id:eq:{_StockItemId}')

    assert _GetResponse.status_code == 200
    assert _GetResponse.json() == []


#endregion delete_stock_item tests
