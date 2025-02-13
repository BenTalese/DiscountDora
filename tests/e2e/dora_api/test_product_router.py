# flake8: noqa

import sys
from dataclasses import asdict
from pathlib import Path
from unittest.mock import ANY

import requests

sys.path.append(str(Path(__file__).resolve().parents[3]))

from framework.dora_api.routes.products.create_product_command import \
    CreateProductCommand

#region ---------------- setup ----------------

base_route = 'http://localhost:5170/api/products'

#endregion setup

#region ---------------- create_product_async tests ----------------

def test__create_product_async__CreatingProductWithAllAttributes__ProductCreated(api):
    _ProductRequest = asdict(CreateProductCommand(
        brand = "Test",
        image = None,
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
    ))

    _Response = requests.post(base_route, json = _ProductRequest)

    assert _Response.status_code == 201
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['id'] == ANY


def test__create_product_async__CreatingProductWithIncorrectDataTypes__ProductCreated(api):
    _ProductRequest = asdict(CreateProductCommand(
        brand = 555,
        image = 234,
        is_active = "AAA",
        is_available = "BBB",
        merchant_name = True,
        merchant_stockcode = 2.3,
        name = 2.4,
        price_now = "CCC",
        price_was = "DDD",
        size = 555,
        size_unit = 2.5,
        size_value = "EEE",
        web_url = False
    ))

    _Response = requests.post(base_route, json = _ProductRequest)

    assert _Response.status_code == 422
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == {}


def test__create_product_async__CreatingProductWithOnlyRequiredAttributes__ProductCreated(api):
    _ProductRequest = CreateProductCommand(
        brand = "Test",
        image = None,
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

    delattr(_ProductRequest, "brand")
    delattr(_ProductRequest, "image")
    delattr(_ProductRequest, "size_value")

    _Response = requests.post(base_route, json = _ProductRequest.__dict__)

    assert _Response.json() == {}
    assert _Response.status_code == 201
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['id'] == ANY


def test__create_product_async__ProductAlreadyExists__IsBusinessRuleViolation(api):
    _ProductRequest = asdict(CreateProductCommand(
        brand = "Test",
        image = None,
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
    ))

    _Response = requests.post(base_route, json = _ProductRequest)

    assert _Response.status_code == 422
    assert _Response.json() == {
       'detail': 'See errors property for more details.',
       'errors': {
           '': [
               "A product with the stockcode '50332BA' from the merchant "
               "'Woolworths' already exists.",
            ],
        },
       'status': 422,
       'title': 'Business rule violation.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }


def test__create_product_async__EmptyRequest__IsRequiredInputsValidationFailure(api):
    _ProductRequest = {}

    _Response = requests.post(base_route, json = _ProductRequest)

    assert _Response.status_code == 422
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
       'detail': 'Required inputs are missing values.',
       'errors': {
           'is_active': [ "'is_active' must have a value." ],
            'is_available': [ "'is_available' must have a value." ],
            'merchant_name': [ "'merchant_name' must have a value." ],
            'merchant_stockcode': [ "'merchant_stockcode' must have a value." ],
            'name': [ "'name' must have a value." ],
            'price_now': [ "'price_now' must have a value." ],
            'price_was': [ "'price_was' must have a value." ],
            'size': [ "'size' must have a value." ],
            'size_unit': [ "'size_unit' must have a value." ],
            'web_url': [ "'web_url' must have a value." ]
        },
       'status': 422,
       'title': 'Validation failure.',
       'type': 'https://datatracker.ietf.org/doc/html/rfc4918#section-11.2',
    }

#endregion create_product_async tests

#region ---------------- get_products_async tests ----------------

def test__get_products_async__GettingAllProducts__GetsAllProducts(api):
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert len(_Response.json()) == 3


def test__get_products_async__FilteringByStockcode__GetsSingleMatchingProduct(api):
    _Response = requests.get(f'{base_route}/filter=merchant_stockcode:eq:50332BA')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()[0]['merchant_stockcode'] == '50332BA'
    assert len(_Response.json()) == 1


def test__get_products_async__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}/filter=stockcode:eq:50332BA')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == {
        'detail': 'Queried attribute(s) do not exist on response: stockcode.',
        'errors': {},
        'status': 400,
        'title': 'Unsupported query operation.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }

# TODO: Also test invalid query syntax, also test not found on e.g. update but also with the get
# TODO: Queried attribute(s) do not exist on response
# TODO: The endpoint "{_RequestEndpoint}" does not support filtering
# TODO: The filter operator {_Operator} is not supported. Supported operators include 'eq', 'lt', 'gt', 'le', 'ge' and 'ne'
# TODO: Sort field {_SortField} does not exist in the view model

#endregion get_products_async tests
