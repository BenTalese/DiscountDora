# flake8: noqa

import sys
from dataclasses import asdict
from multiprocessing import Process
from pathlib import Path
from time import sleep
from unittest.mock import ANY

import pytest_asyncio
import requests

sys.path.append(str(Path(__file__).resolve().parents[3]))

from framework.dora_api.app import app
from framework.dora_api.routes.products.create_product_command import \
    CreateProductCommand
from framework.dora_api.startup import startup

#region ---------------- setup ----------------

base_route = 'http://localhost:5170/api/products'


def run_api():
    app.run('localhost', 5170)


@pytest_asyncio.fixture(scope="session")
async def api():
    await startup(is_test_env = True)
    process = Process(target=run_api)
    process.start()
    sleep(3)

    yield

    process.terminate()
    process.join()

#endregion setup

#region ---------------- create_product_async Tests ----------------

def test__create_product_async__CreatingNewProduct__ProductCreated(api):
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
    assert _Response.json()['id'] == ANY


def test__create_product_async__ProductAlreadyExists__BusinessRuleViolation(api):
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

#endregion create_product_async Tests

