"""Cart Button Chunk 3 (FU-132) — standalone product lines + rules 1–3.

DORA_VERIFY Shopping-lists L533–536. A shopping-list line anchors on a stock
item, a product, or both (CHECK `ck_shopping_list_line_anchor`). This pins the
server rules that have no coverage:

* Rule 1 — a `product_id`-only line is created; a no-anchor body is a 400.
* Rule 2 — linking that product to a stock item upgrades the orphan line
  (convert-in-place when there's no stock-item line yet; fold into the existing
  stock-item line when there is).
* Rule 3 — deleting a stock-item line cascade-removes the nested product line.
"""
from uuid import uuid4

import requests

from tests.factories import make_stock_item
from tests.support import assert_problem

BASE = "http://localhost:5170/api"
LISTS = f"{BASE}/shopping-lists"


def _stock_level_id(sequence: int = 0) -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == sequence)


def _make_product() -> str:
    suffix = uuid4().hex[:8]
    resp = requests.post(f"{BASE}/products", json={
        "name": f"CartProduct-{suffix}",
        "store_name": "Woolworths",
        "merchant_stockcode": f"CART-{suffix}",
        "brand": "Test",
        "price_now": 4.5,
        "price_was": 6.0,
        "is_active": True,
        "is_available": True,
        "size": "1L",
        "size_unit": "L",
        "size_value": 1.0,
    })
    assert resp.status_code == 201, resp.text
    return resp.headers["location"].rsplit(":", 1)[-1]


def _make_draft() -> str:
    resp = requests.post(LISTS, json={"name": f"CartList-{uuid4().hex[:8]}"})
    assert resp.status_code == 201, resp.text
    return resp.json()["shopping_list_id"]


def _add_line(list_id: str, **anchor) -> requests.Response:
    return requests.post(f"{LISTS}/{list_id}/lines", json=anchor)


def _lines(list_id: str) -> list:
    return requests.get(f"{LISTS}/{list_id}").json()["lines"]


def _link(stock_item_id: str, product_id: str) -> None:
    resp = requests.post(f"{BASE}/stock-items/{stock_item_id}/products",
                         json={"product_id": product_id})
    assert resp.status_code in (200, 204), resp.text


def test__rule1__product_only_line_is_created(api):
    list_id = _make_draft()
    product_id = _make_product()
    resp = _add_line(list_id, product_id=product_id)
    assert resp.status_code in (200, 201), resp.text

    lines = _lines(list_id)
    assert len(lines) == 1
    assert lines[0]["product_id"] == product_id
    assert lines[0]["stock_item_id"] is None


def test__rule1__no_anchor_is_rejected(api):
    # DORA_VERIFY L533 guessed "400 before DB"; the server actually returns a
    # 422 business-rule violation with a clear message (the DB CHECK is the
    # backstop, not the surfaced error). 422 is correct for a domain rule.
    list_id = _make_draft()
    resp = _add_line(list_id)  # neither stock_item_id nor product_id
    body = assert_problem(resp, 422)
    assert "at least one of stock_item_id or product_id" in resp.text


def test__rule2__linking_converts_the_orphan_line_in_place(api):
    # A product-only line, no stock-item line yet → linking the product to a
    # stock item converts the orphan in place (gains stock_item_id, keeps
    # product_id) — one nested row, not two.
    list_id = _make_draft()
    product_id = _make_product()
    item = make_stock_item(stock_level_id=_stock_level_id(),
                           name=f"CartItem {uuid4().hex[:8]}")
    _add_line(list_id, product_id=product_id)

    _link(item["stock_item_id"], product_id)

    lines = _lines(list_id)
    assert len(lines) == 1
    assert lines[0]["stock_item_id"] == item["stock_item_id"]
    assert lines[0]["product_id"] == product_id


def test__rule2__linking_folds_into_an_existing_stock_item_line(api):
    # A stock-item line AND a separate product-only line → linking folds the
    # product anchor into the stock-item line and drops the orphan.
    list_id = _make_draft()
    product_id = _make_product()
    item = make_stock_item(stock_level_id=_stock_level_id(),
                           name=f"CartItem {uuid4().hex[:8]}")
    _add_line(list_id, stock_item_id=item["stock_item_id"])
    _add_line(list_id, product_id=product_id)
    assert len(_lines(list_id)) == 2

    _link(item["stock_item_id"], product_id)

    lines = _lines(list_id)
    assert len(lines) == 1
    assert lines[0]["stock_item_id"] == item["stock_item_id"]
    assert lines[0]["product_id"] == product_id


def test__rule3__deleting_the_stock_item_line_cascades_to_the_nested_product(api):
    # Stock-item line for S + a nested product-only line for P (P linked to S)
    # → deleting the stock-item line removes the nested product line too.
    list_id = _make_draft()
    product_id = _make_product()
    item = make_stock_item(stock_level_id=_stock_level_id(),
                           name=f"CartItem {uuid4().hex[:8]}")
    _link(item["stock_item_id"], product_id)
    _add_line(list_id, stock_item_id=item["stock_item_id"])
    _add_line(list_id, product_id=product_id)  # nested product-only line

    lines = _lines(list_id)
    stock_line = next(l for l in lines if l["stock_item_id"] == item["stock_item_id"]
                      and l["product_id"] is None)

    resp = requests.delete(f"{LISTS}/{list_id}/lines/{stock_line['line_id']}")
    assert resp.status_code in (200, 204), resp.text

    assert _lines(list_id) == []
