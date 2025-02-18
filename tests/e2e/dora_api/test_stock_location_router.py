import uuid
import requests

from tests.support import is_valid_uuid

#region ---------------- setup ----------------

base_route = 'http://localhost:5170/api/stock-locations'

#endregion setup

#region ---------------- create_stock_location_async tests ----------------

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
