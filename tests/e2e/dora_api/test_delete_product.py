"""Batch C — product hard delete, via both front doors.

Feedback L197 ("no way to remove a saved product"). One behaviour
(`DeleteProductHandler`), two authenticated routes: the SPA's session-authed
`DELETE /api/products/<id>` and the companion's bearer-authed
`DELETE /api/ingest/products/<id>` (PF-4).

Pinned here: the cascade takes everything hanging off the product (offers,
history, alerts, barcode, stock-item link) while leaving the stock item itself
alone; finished shopping lists keep their line; live lists lose it; and the
bearer door refuses an absent or wrong key.
"""
from uuid import uuid4

import requests

from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"
LISTS = f"{BASE}/shopping-lists"


def _stock_level_id(sequence: int = 0) -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == sequence)


def _make_product(name: str = "Doomed") -> str:
    suffix = uuid4().hex[:8]
    resp = requests.post(f"{BASE}/products", json={
        "name": f"{name}-{suffix}",
        "store_name": "Woolworths",
        "merchant_stockcode": f"DEL-{suffix}",
        "brand": "Test",
        "price_now": 2.5,
        "price_was": 5.0,
        "is_active": True,
        "is_available": True,
        "size": "1L",
        "size_unit": "L",
        "size_value": 1.0,
    })
    assert resp.status_code == 201, resp.text
    return resp.headers["location"].rsplit(":", 1)[-1]


def _product_ids() -> set[str]:
    return {
        p["product_id"]
        for p in requests.get(f"{BASE}/products").json()["items"]
    }


def _mint_key() -> str:
    resp = requests.post(f"{BASE}/ingestion-sources", json={
        "label": f"companion-{uuid4().hex[:8]}",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["key"]


def _make_list() -> str:
    resp = requests.post(LISTS, json={"name": f"L-{uuid4().hex[:8]}"})
    assert resp.status_code == 201, resp.text
    return resp.json()["shopping_list_id"]


def _add_line(list_id: str, **anchor) -> str:
    resp = requests.post(f"{LISTS}/{list_id}/lines", json=anchor)
    assert resp.status_code == 200, resp.text
    return resp.json()["line_id"]


def _lines(list_id: str) -> list[dict]:
    return requests.get(f"{LISTS}/{list_id}").json()["lines"]


# ── SPA door ───────────────────────────────────────────────────────────

def test__delete_product__removes_it_from_the_catalogue():
    product_id = _make_product()
    assert product_id in _product_ids()

    resp = requests.delete(f"{BASE}/products/{product_id}")

    assert resp.status_code == 204, resp.text
    assert product_id not in _product_ids()


def test__delete_product__unknown_id_is_404():
    resp = requests.delete(f"{BASE}/products/{uuid4()}")

    assert resp.status_code == 404


def test__delete_product__drops_the_link_but_keeps_the_stock_item():
    """The link is the product's, the stock item is the user's pantry."""
    item_id = make_stock_item(
        stock_level_id=_stock_level_id(), name=f"Keeper-{uuid4().hex[:8]}",
    )["stock_item_id"]
    product_id = _make_product()
    linked = requests.post(
        f"{BASE}/stock-items/{item_id}/products", json={"product_id": product_id},
    )
    assert linked.status_code in (200, 201, 204), linked.text

    assert requests.delete(f"{BASE}/products/{product_id}").status_code == 204

    detail = requests.get(f"{BASE}/stock-items/{item_id}/detail")
    assert detail.status_code == 200, "the stock item went with the product"
    assert all(
        p["product_id"] != product_id for p in detail.json()["products"]
    ), "a deleted product is still linked"


def test__delete_product__finished_list_keeps_its_line():
    """D-4 / FU-883 — the receipt survives, still naming what was bought."""
    product_id = _make_product("Receipted")
    name = next(
        p["name"] for p in requests.get(f"{BASE}/products").json()["items"]
        if p["product_id"] == product_id
    )
    list_id = _make_list()
    _add_line(list_id, product_id=product_id)
    assert requests.post(f"{LISTS}/{list_id}/finish", json={}).status_code == 200

    assert requests.delete(f"{BASE}/products/{product_id}").status_code == 204

    lines = _lines(list_id)
    assert len(lines) == 1, "the receipt lost its line"
    assert lines[0]["product_id"] is None
    assert lines[0]["stock_item_name"] == name


def test__delete_product__live_list_loses_its_line():
    product_id = _make_product("Planned")
    list_id = _make_list()
    _add_line(list_id, product_id=product_id)

    assert requests.delete(f"{BASE}/products/{product_id}").status_code == 204

    assert _lines(list_id) == []


# ── Companion (bearer) door ────────────────────────────────────────────

def test__ingest_delete__with_a_valid_key_deletes():
    key = _mint_key()
    product_id = _make_product("Unsaved")

    resp = requests.delete(
        f"{BASE}/ingest/products/{product_id}",
        headers={"Authorization": f"Bearer {key}"},
    )

    assert resp.status_code == 204, resp.text
    assert product_id not in _product_ids()


def test__ingest_delete__without_a_key_is_401():
    product_id = _make_product("Guarded")

    resp = requests.Session().delete(f"{BASE}/ingest/products/{product_id}")

    assert resp.status_code == 401
    assert product_id in _product_ids(), "an unauthenticated call still deleted"


def test__ingest_delete__with_a_bad_key_is_401():
    product_id = _make_product("Guarded")

    resp = requests.Session().delete(
        f"{BASE}/ingest/products/{product_id}",
        headers={"Authorization": "Bearer not-a-real-key"},
    )

    assert resp.status_code == 401
    assert product_id in _product_ids()


def test__ingest_delete__unknown_product_is_404():
    key = _mint_key()

    resp = requests.delete(
        f"{BASE}/ingest/products/{uuid4()}",
        headers={"Authorization": f"Bearer {key}"},
    )

    assert resp.status_code == 404
