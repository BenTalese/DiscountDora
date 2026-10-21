"""A template line carries the list row's "which one" choice (2026-10-14).

The template editor offers the same picker as a list row: offers on products
installs, preferred buys otherwise. Instantiating copies the choice onto the
new list while it still applies, and unlinking the product clears it.
"""
from uuid import uuid4

import requests

from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"
SL_TEMPLATES = f"{BASE}/shopping-list-templates"
LISTS = f"{BASE}/shopping-lists"
STOCK_ITEMS = f"{BASE}/stock-items"


def _stock_level_id() -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == 0)


def _new_item() -> str:
    return make_stock_item(stock_level_id=_stock_level_id(),
                           name=f"TplChoiceItem {uuid4().hex[:8]}")["stock_item_id"]


def _make_product() -> str:
    suffix = uuid4().hex[:8]
    resp = requests.post(f"{BASE}/products", json={
        "name": f"TplChoiceProduct-{suffix}",
        "store_name": "Woolworths",
        "merchant_stockcode": f"TPL-{suffix}",
        "brand": "Test",
        "price_now": 3.0,
        "price_was": 4.0,
        "is_active": True,
        "is_available": True,
        "size": "1L",
        "size_unit": "L",
        "size_value": 1.0,
    })
    assert resp.status_code == 201, resp.text
    return resp.headers["location"].rsplit(":", 1)[-1]


def _link(item_id: str, product_id: str) -> None:
    resp = requests.post(f"{STOCK_ITEMS}/{item_id}/products", json={"product_id": product_id})
    assert resp.status_code in (200, 204), resp.text


def _template_with(item_id: str) -> str:
    resp = requests.post(SL_TEMPLATES, json={
        "name": f"TplChoice {uuid4().hex[:8]}",
        "lines": [{"stock_item_id": item_id, "quantity": 2}],
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["template_id"]


def _template_line(template_id: str) -> dict:
    return requests.get(f"{SL_TEMPLATES}/{template_id}").json()["lines"][0]


def _patch(template_id: str, line_id: str, body: dict) -> requests.Response:
    return requests.patch(f"{SL_TEMPLATES}/{template_id}/lines/{line_id}", json=body)


def _instantiate(template_id: str) -> dict:
    resp = requests.post(f"{SL_TEMPLATES}/{template_id}/instantiate", json={})
    assert resp.status_code == 200, resp.text
    return requests.get(f"{LISTS}/{resp.json()['shopping_list_id']}").json()["lines"][0]


def test__template_detail__lists_the_items_offers_and_preferred_buys(api):
    item = _new_item()
    product = _make_product()
    _link(item, product)
    requests.post(f"{STOCK_ITEMS}/{item}/preferred-buys", json={"label": "Brand A"})

    line = _template_line(_template_with(item))

    assert [o["product_id"] for o in line["offers"]] == [product]
    assert [pb["label"] for pb in line["preferred_buys"]] == ["Brand A"]
    assert line["selected_product_id"] is None


def test__picked_offer__carries_to_the_new_list_with_its_store(api):
    item = _new_item()
    product = _make_product()
    _link(item, product)
    template = _template_with(item)
    line = _template_line(template)

    assert _patch(template, line["line_id"], {"selected_product_id": product}).status_code == 204
    assert _template_line(template)["selected_product_id"] == product

    new_line = _instantiate(template)
    assert new_line["selected_product_id"] == product
    assert new_line["planned_store_id"] == new_line["offers"][0]["store_id"]
    assert new_line["quantity"] == 2


def test__preferred_buy__carries_to_the_new_list(api):
    item = _new_item()
    requests.post(f"{STOCK_ITEMS}/{item}/preferred-buys", json={"label": "Brand A"})
    template = _template_with(item)
    line = _template_line(template)
    pb_id = line["preferred_buys"][0]["preferred_buy_id"]

    assert _patch(template, line["line_id"], {"preferred_buy_id": pb_id}).status_code == 204
    assert _instantiate(template)["preferred_buy_id"] == pb_id

    assert _patch(template, line["line_id"], {"preferred_buy_id": None}).status_code == 204
    assert _template_line(template)["preferred_buy_id"] is None


def test__unlinked_product__is_rejected_as_a_choice(api):
    item = _new_item()
    stranger = _make_product()
    template = _template_with(item)
    line = _template_line(template)

    assert _patch(template, line["line_id"], {"selected_product_id": stranger}).status_code == 422


def test__unlinking_the_product__clears_the_template_choice(api):
    item = _new_item()
    product = _make_product()
    _link(item, product)
    template = _template_with(item)
    line = _template_line(template)
    _patch(template, line["line_id"], {"selected_product_id": product})

    assert requests.delete(f"{STOCK_ITEMS}/{item}/products/{product}").status_code == 204

    assert _template_line(template)["selected_product_id"] is None
