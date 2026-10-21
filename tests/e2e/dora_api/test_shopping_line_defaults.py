"""A new line remembers what you chose for the item last time (2026-09-27).

Pins `_line_defaults.apply_line_defaults` through the add paths, plus the two
rules that make a picked offer mean something: it moves the line to the offer's
store, and it prices the line's estimate above what you last paid.
"""
from uuid import uuid4

import requests

from tests.factories import make_stock_item
from tests.support import assert_problem

BASE = "http://localhost:5170/api"
LISTS = f"{BASE}/shopping-lists"
STOCK_ITEMS = f"{BASE}/stock-items"


def _stock_level_id() -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == 0)


def _new_item() -> str:
    return make_stock_item(stock_level_id=_stock_level_id(),
                           name=f"DefaultsItem {uuid4().hex[:8]}")["stock_item_id"]


def _make_product(price_now: float = 4.5) -> str:
    suffix = uuid4().hex[:8]
    resp = requests.post(f"{BASE}/products", json={
        "name": f"DefaultsProduct-{suffix}",
        "store_name": "Woolworths",
        "merchant_stockcode": f"DEF-{suffix}",
        "brand": "Test",
        "price_now": price_now,
        "price_was": 6.0,
        "is_active": True,
        "is_available": True,
        "size": "1L",
        "size_unit": "L",
        "size_value": 1.0,
    })
    assert resp.status_code == 201, resp.text
    return resp.headers["location"].rsplit(":", 1)[-1]


def _link(item_id: str, product_id: str) -> None:
    resp = requests.post(f"{STOCK_ITEMS}/{item_id}/products",
                         json={"product_id": product_id})
    assert resp.status_code in (200, 204), resp.text


def _make_draft() -> str:
    resp = requests.post(LISTS, json={"name": f"DefaultsList-{uuid4().hex[:8]}"})
    assert resp.status_code == 201, resp.text
    return resp.json()["shopping_list_id"]


def _add(list_id: str, item_id: str) -> None:
    resp = requests.post(f"{LISTS}/{list_id}/lines", json={"stock_item_id": item_id})
    assert resp.status_code in (200, 201), resp.text


def _line(list_id: str) -> dict:
    return requests.get(f"{LISTS}/{list_id}").json()["lines"][0]


def _patch(list_id: str, line_id: str, body: dict) -> requests.Response:
    return requests.patch(f"{LISTS}/{list_id}/lines/{line_id}", json=body)


def test__preferred_buy__carries_over_to_the_next_list(api):
    item = _new_item()
    assert requests.post(f"{STOCK_ITEMS}/{item}/preferred-buys",
                         json={"label": "Vitasoy Oat Milky 1L"}).status_code == 204
    pb_id = requests.get(f"{STOCK_ITEMS}/{item}/detail").json()["preferred_buys"][0]["preferred_buy_id"]

    first = _make_draft()
    _add(first, item)
    _patch(first, _line(first)["line_id"], {"preferred_buy_id": pb_id})

    second = _make_draft()
    _add(second, item)
    assert _line(second)["preferred_buy_id"] == pb_id


def test__cleared_choice__is_remembered_as_cleared(api):
    item = _new_item()
    requests.post(f"{STOCK_ITEMS}/{item}/preferred-buys", json={"label": "Brand A"})
    pb_id = requests.get(f"{STOCK_ITEMS}/{item}/detail").json()["preferred_buys"][0]["preferred_buy_id"]

    first = _make_draft()
    _add(first, item)
    _patch(first, _line(first)["line_id"], {"preferred_buy_id": pb_id})
    second = _make_draft()
    _add(second, item)
    _patch(second, _line(second)["line_id"], {"clear_preferred_buy": True})

    third = _make_draft()
    _add(third, item)
    assert _line(third)["preferred_buy_id"] is None


def test__picked_offer__carries_over_with_its_store(api):
    item = _new_item()
    product = _make_product()
    _link(item, product)

    first = _make_draft()
    _add(first, item)
    _patch(first, _line(first)["line_id"], {"selected_product_id": product})

    second = _make_draft()
    _add(second, item)
    line = _line(second)
    assert line["selected_product_id"] == product
    assert line["planned_store_id"] == line["offers"][0]["store_id"]


def test__picking_an_offer__moves_the_line_to_its_store(api):
    item = _new_item()
    product = _make_product()
    _link(item, product)
    list_id = _make_draft()
    _add(list_id, item)
    line = _line(list_id)
    assert line["planned_store_id"] is None

    _patch(list_id, line["line_id"], {"selected_product_id": product})
    after = _line(list_id)
    assert after["planned_store_id"] == after["offers"][0]["store_id"]

    # Un-picking leaves the store where it is.
    _patch(list_id, line["line_id"], {"clear_selected_product": True})
    assert _line(list_id)["planned_store_id"] == after["offers"][0]["store_id"]


def test__picked_offer__prices_the_estimate_and_unpicking_restores_it(api):
    item = _new_item()
    product = _make_product(price_now=3.25)
    _link(item, product)
    list_id = _make_draft()
    _add(list_id, item)
    line = _line(list_id)
    # An offer nobody picked does not price the line.
    assert line["estimate_source"] == "none"
    assert line["estimated_unit_price"] is None

    _patch(list_id, line["line_id"], {"selected_product_id": product})
    picked = _line(list_id)
    assert picked["estimate_source"] == "offer"
    assert picked["estimated_unit_price"] == 3.25

    _patch(list_id, line["line_id"], {"clear_selected_product": True})
    assert _line(list_id)["estimate_source"] == "none"


def test__quantity_below_one__is_rejected(api):
    item = _new_item()
    list_id = _make_draft()
    _add(list_id, item)
    resp = _patch(list_id, _line(list_id)["line_id"], {"quantity": 0})
    assert_problem(resp, 400)
