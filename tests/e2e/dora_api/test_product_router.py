import uuid
from unittest.mock import ANY

import requests

from dora_api.features.products.create_product import CreateProductRequest
from dora_api.features.products.update_product import UpdateProductRequest
from tests.support import is_valid_uuid

#region ---------------- setup ----------------

base_route = 'http://localhost:5170/api/products'

#endregion setup

#region ---------------- create_product_async tests ----------------


# TODO: Write test for optional fields (brand, stockcode, etc)
def test__create_product__CreatingProductWithAllAttributes__ProductCreated(api):
    _ProductRequest = CreateProductRequest(
        brand = "Test",
        image = None,  # TODO: Grab a random image, maybe dora icon from repo
        is_active = True,
        is_available = True,
        merchant_name = "Woolworths",
        merchant_stockcode = "50332BA",
        name = "Banana Mangoes",
        price_now = 4.5,
        price_was = 10.5,
        size = "500g",
        size_unit = "g",
        size_value = 5.0,
        web_url = "www"
    )

    _Response = requests.post(base_route, json = _ProductRequest.model_dump())

    assert _Response.status_code == 201
    assert _Response.headers['Content-Type'] == 'application/json'
    assert 'http://localhost:5170/api/products/filter=product_id:eq:' in _Response.headers['location']
    assert _Response.json()['id'] == ANY


def test__create_product__CreatingProductWithIncorrectDataTypes__CannotBeDeserialised(api):
    _Request = {
        "brand": 555,
        "image": 234,
        "is_active": "AAA",
        "is_available": "BBB",
        "merchant_name": True,
        "merchant_stockcode": 2.3,
        "name": 2.4,
        "price_now": "CCC",
        "price_was": "DDD",
        "size": 555,
        "size_unit": 2.5,
        "size_value": "EEE",
        "web_url": False
    }

    _Response = requests.post(base_route, json = _Request)
    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": "See errors property for more details.",
        "errors": {
            "brand": ["Input should be a valid string"],
            "image": ["Input should be a valid bytes"],
            "is_active": ["Input should be a valid boolean, unable to interpret input"],
            "is_available": ["Input should be a valid boolean, unable to interpret input"],
            "merchant_name": ["Input should be a valid string"],
            "merchant_stockcode": ["Input should be a valid string"],
            "name": ["Input should be a valid string"],
            "price_now": ["Input should be a valid number, unable to parse string as a number"],
            "price_was": ["Input should be a valid number, unable to parse string as a number"],
            "size": ["Input should be a valid string"],
            "size_unit": ["Input should be a valid string"],
            "size_value": ["Input should be a valid number, unable to parse string as a number"],
            "web_url": ["Input should be a valid string"]
        },
        "status": 400,
        "title": "Malformed request.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__create_product__CreatingProductWithOnlyRequiredAttributes__ProductCreated(api):
    _ProductRequest = CreateProductRequest(
        is_active = True,
        is_available = True,
        merchant_name = "Woolworths",
        name = "Milo Chocolate Powder",
        price_now = 4.5,
        price_was = 10.5,
        size = "500g",
        size_unit = "g",
        size_value = 5.0
    )

    _Response = requests.post(base_route, json = _ProductRequest.model_dump())

    assert _Response.status_code == 201
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['id'] == ANY


def test__create_product__ProductAlreadyExists__IsBusinessRuleViolation(api):
    _ProductRequest = CreateProductRequest(
        brand = "Test",
        image = None,
        is_active = True,
        is_available = True,
        merchant_name = "WoolWorThS",
        merchant_stockcode = "50332ba",
        name = "Banana Mangoes",
        price_now = 4.5,
        price_was = 10.5,
        size = "500g",
        size_unit = "g",
        size_value = 5.0,
        web_url = "www"
    )

    _Response = requests.post(base_route, json = _ProductRequest.model_dump())

    assert _Response.status_code == 422
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {'': ["Product already exists with name 'Banana Mangoes', merchant 'WoolWorThS', and stockcode '50332ba'."]},
       'status': 422,
       'title': 'Business rule violation.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }


def test__create_product__ExtraAttributes__IsBadRequest(api):
    _ProductRequest = {
        "brand": "Test",
        "image": None,
        "is_active": True,
        "is_available": True,
        "merchant_name": "WoolWorThS",
        "merchant_stockcode": "50332ba",
        "name": "Banana Mangoes",
        "price_now": 4.5,
        "price_was": 10.5,
        "size": "500g",
        "size_unit": "g",
        "size_value": 5.0,
        "web_url": "www",
        "poopusgoopus": "aaaa"
    }

    _Response = requests.post(base_route, json = _ProductRequest)

    assert _Response.status_code == 400
    assert _Response.json() == {
        "detail": "See errors property for more details.",
        "errors": {
            "poopusgoopus": ["Extra inputs are not permitted"]
        },
        "status": 400,
        "title": "Malformed request.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"
    }


def test__create_product__EmptyRequest__IsRequiredInputsValidationFailure(api):
    _Response = requests.post(base_route, json = {})

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {
            'is_active': ["Field required"],
            'is_available': ["Field required"],
            'merchant_name': ["Field required"],
            'name': ["Field required"],
            'price_now': ["Field required"],
            'price_was': ["Field required"],
            'size': ["Field required"],
            'size_unit': ["Field required"],
            'size_value': ["Field required"],
        },
       'status': 400,
       'title': 'Malformed request.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


#endregion create_product_async tests

#region ---------------- get_products_async tests ----------------


def test__get_products__GettingProduct__GetsAllExpectedAttributes(api):
    _Product = requests.get(f'{base_route}/filter=merchant_stockcode:eq:50332BA').json()[0]

    assert _Product['brand'] == 'Test'
    assert _Product['image'] is None
    assert _Product['is_active'] is True
    assert _Product['is_available'] is True
    assert is_valid_uuid(_Product['merchant_id'])
    assert _Product['merchant_name'] == 'Woolworths'
    assert _Product['merchant_stockcode'] == '50332BA'
    assert _Product['name'] == 'Banana Mangoes'
    assert _Product['price_now'] == 4.5
    assert _Product['price_was'] == 10.5
    assert is_valid_uuid(_Product['product_id'])
    assert _Product['size'] == '500g'
    assert _Product['size_unit'] == 'g'
    assert _Product['size_value'] == 5.0
    assert _Product['web_url'] == 'www'
    assert _Product.keys() == {
        'brand',
        'image',
        'is_active',
        'is_available',
        'merchant_id',
        'merchant_name',
        'merchant_stockcode',
        'name',
        'price_now',
        'price_was',
        'product_id',
        'size',
        'size_unit',
        'size_value',
        'web_url'
    }


def test__get_products__GettingAllProducts__GetsAllProducts(api):
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert len(_Response.json()) == 4


def test__get_products__FilteringByStockcode__GetsSingleMatchingProduct(api):
    _Response = requests.get(f'{base_route}/filter=merchant_stockcode:eq:50332BA')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['merchant_stockcode'] == '50332BA'
    assert len(_Response.json()) == 1


def test__get_products__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=stockcode:eq:50332BA')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'Queried attribute(s) do not exist on response: stockcode.',
        'errors': {},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_products__FilteringForProductThatDoesNotExist__EmptyResult(api):
    _Response = requests.get(f'{base_route}/filter=product_id:eq:{uuid.uuid4()}')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == []


def test__get_products__FilteringWithUnsupportedOperator__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=product_id:xx:{uuid.uuid4()}')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': "The filter operator 'xx' is not supported. Supported operators: 'eq', 'ne', 'lt', 'gt', 'le', 'ge', 'ct'.",
        'errors': {},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_products__SortingByNonExistentAttribute__IsBadRequest(api):
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


#endregion get_products_async tests

#region ---------------- update_product_async tests ----------------


def test__update_product__EmptyUpdate__ProductUnaffected(api):
    _ProductToUpdate = requests.get(f'{base_route}/filter=merchant_stockcode:eq:50332BA').json()[0]
    _PatchResponse = requests.patch(f"{base_route}/{_ProductToUpdate['product_id']}", json = {})
    _ProductAfterPatchOperation = requests.get(f'{base_route}/filter=merchant_stockcode:eq:50332BA').json()[0]

    assert _PatchResponse.status_code == 204
    assert _PatchResponse.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert _ProductToUpdate == _ProductAfterPatchOperation


def test__update_product__UpdatingAllAttributes__AllAttributesUpdated(api):
    _ProductToUpdate = requests.get(f'{base_route}/filter=merchant_stockcode:eq:51741').json()[0]

    _ProductRequest = UpdateProductRequest(
        is_active = False,
        is_available = False,
        price_now = 1.0,
        price_was = 12.8
    )

    _PatchResponse = requests.patch(f"{base_route}/{_ProductToUpdate['product_id']}", json = _ProductRequest.model_dump())
    _ProductAfterPatchOperation = requests.get(f'{base_route}/filter=merchant_stockcode:eq:51741').json()[0]

    assert _PatchResponse.status_code == 204
    assert _PatchResponse.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert _ProductToUpdate == {
        'brand': 'Cadbury',
        'image': None,
        'is_active': True,
        'is_available': True,
        'merchant_name': 'Woolworths',
        'merchant_id': _ProductToUpdate['merchant_id'],
        'merchant_stockcode': '51741',
        'name': 'Cadbury Freddo Cake',
        'price_now': 2.82,
        'price_was': 3.52,
        'size': '1.5L',
        'size_unit': 'L',
        'size_value': 1.0,
        'web_url': 'https://www.woolworths.com.au/shop/productdetails/51741',
        'product_id': _ProductToUpdate['product_id']
    }
    assert _ProductAfterPatchOperation == {
        'brand': 'Cadbury',
        'image': None,
        'is_active': False,
        'is_available': False,
        'merchant_name': 'Woolworths',
        'merchant_id': _ProductToUpdate['merchant_id'],
        'merchant_stockcode': '51741',
        'name': 'Cadbury Freddo Cake',
        'price_now': 1.0,
        'price_was': 12.8,
        'size': '1.5L',
        'size_unit': 'L',
        'size_value': 1.0,
        'web_url': 'https://www.woolworths.com.au/shop/productdetails/51741',
        'product_id': _ProductToUpdate['product_id']
    }


def test__update_product__ProductDoesNotExist__ProductNotFound(api):
    _RandomID = uuid.uuid4()
    _Response = requests.patch(f"{base_route}/{_RandomID}", json = {})

    assert _Response.status_code == 404
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        "detail": f"Product with the ID '{_RandomID}' was not found.",
        "errors": {},
        "status": 404,
        "title": "Entity was not found.",
        "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4"
    }


def test__update_product__UpdatingPriceNowWithoutPriceWas__IsValidationFailure(api):
    _ProductToUpdate = requests.get(f'{base_route}/filter=merchant_stockcode:eq:50332BA').json()[0]

    _ProductRequest = UpdateProductRequest(price_now = 1.0).model_dump(exclude_unset=True)

    _PatchResponse = requests.patch(f"{base_route}/{_ProductToUpdate['product_id']}", json = _ProductRequest)
    _ProductAfterPatchOperation = requests.get(f'{base_route}/filter=merchant_stockcode:eq:50332BA').json()[0]

    assert _ProductToUpdate == _ProductAfterPatchOperation
    assert _PatchResponse.status_code == 422
    assert _PatchResponse.headers['Content-Type'] == 'application/problem+json'
    assert _PatchResponse.json() == {
        "detail": "See errors property for more details.",
        "errors": {
            "": ["price_now and price_was must both be set."]
        },
        "status": 422,
        "title": "Business rule violation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"
    }


def test__update_product__UpdatingPriceWasWithoutPriceNow__IsValidationFailure(api):
    _ProductToUpdate = requests.get(f'{base_route}/filter=merchant_stockcode:eq:50332BA').json()[0]

    _ProductRequest = UpdateProductRequest(price_was = 1.0).model_dump(exclude_unset=True)

    _PatchResponse = requests.patch(f"{base_route}/{_ProductToUpdate['product_id']}", json = _ProductRequest)
    _ProductAfterPatchOperation = requests.get(f'{base_route}/filter=merchant_stockcode:eq:50332BA').json()[0]

    assert _ProductToUpdate == _ProductAfterPatchOperation
    assert _PatchResponse.status_code == 422
    assert _PatchResponse.headers['Content-Type'] == 'application/problem+json'
    assert _PatchResponse.json() == {
        "detail": "See errors property for more details.",
        "errors": {
            "": ["price_now and price_was must both be set."]
        },
        "status": 422,
        "title": "Business rule violation.",
        "type": "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"
    }


#endregion update_product_async tests
