"""FU-519 — shared seeding for spend-shaped e2e suites (budget / reports).

Creates a fully-priced purchase through the HTTP boundary (R-005): a unique
store + product, a stock item, a shopping list whose line selects the product
(which snapshots ``picked_offer_price`` / ``list_price_at_pick`` at add time),
optionally ticks / overrides the till price / archives the list. Every id is
suffixed so tests never collide with the dev seed or each other.
"""
from __future__ import annotations

import uuid

import requests

BASE = "http://localhost:5170/api"


def seed_purchase(
    *,
    price_now: float = 4.5,
    price_was: float = 10.5,
    quantity: int | None = None,
    actual_unit_price: float | None = None,
    stock_group_id: str | None = None,
    stock_item_id: str | None = None,
    tick: bool = True,
    finish: bool = True,
) -> dict:
    """Seed one purchase; returns the ids/names a test needs to find its own
    rows in report/budget aggregates. Pass ``stock_item_id`` to put an
    existing item on a *second* list (most-bought scenarios)."""
    suffix = uuid.uuid4().hex[:8]
    store_name = f"SpendStore-{suffix}"

    resp = requests.post(f"{BASE}/stores", json={"name": store_name})
    assert resp.status_code == 201, resp.text
    stores = requests.get(f"{BASE}/stores").json()["items"]
    store_id = next(s["store_id"] for s in stores if s["name"] == store_name)

    product_resp = requests.post(f"{BASE}/products", json={
        "name": f"SpendProduct-{suffix}",
        "store_name": store_name,
        "merchant_stockcode": f"SPEND-{suffix}",
        "brand": "Test",
        "price_now": price_now,
        "price_was": price_was,
        "is_active": True,
        "is_available": True,
        "size": "1L",
        "size_unit": "L",
        "size_value": 1.0,
    })
    assert product_resp.status_code == 201, product_resp.text
    # Location header shape: /api/products?filter=product_id:eq:<uuid>
    product_id = product_resp.headers["location"].rsplit(":", 1)[-1]

    stock_item_name = None
    if stock_item_id is None:
        level = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
        stock_item_name = f"SpendItem-{suffix}"
        body: dict = {"name": stock_item_name, "stock_level_id": level}
        if stock_group_id is not None:
            body["stock_group_id"] = stock_group_id
        stock_resp = requests.post(f"{BASE}/stock-items", json=body)
        assert stock_resp.status_code == 201, stock_resp.text
        stock_item_id = stock_resp.json()["stock_item_id"]

    list_resp = requests.post(
        f"{BASE}/shopping-lists", json={"name": f"SpendList-{suffix}"},
    )
    assert list_resp.status_code == 201, list_resp.text
    list_id = list_resp.json()["shopping_list_id"]

    line_resp = requests.post(
        f"{BASE}/shopping-lists/{list_id}/lines",
        json={"stock_item_id": stock_item_id, "selected_product_id": product_id},
    )
    assert line_resp.status_code in (200, 201), line_resp.text
    line_id = requests.get(f"{BASE}/shopping-lists/{list_id}").json()["lines"][0]["line_id"]

    patch: dict = {}
    if tick:
        patch["is_ticked"] = True
    if quantity is not None:
        patch["quantity"] = quantity
    if actual_unit_price is not None:
        patch["actual_unit_price"] = actual_unit_price
    if patch:
        patch_resp = requests.patch(
            f"{BASE}/shopping-lists/{list_id}/lines/{line_id}", json=patch,
        )
        assert patch_resp.status_code == 204, patch_resp.text

    if finish:
        finish_resp = requests.post(f"{BASE}/shopping-lists/{list_id}/finish")
        assert finish_resp.status_code == 200, finish_resp.text

    return {
        "suffix": suffix,
        "store_id": store_id,
        "store_name": store_name,
        "product_id": product_id,
        "stock_item_id": stock_item_id,
        "stock_item_name": stock_item_name,
        "shopping_list_id": list_id,
        "line_id": line_id,
    }
