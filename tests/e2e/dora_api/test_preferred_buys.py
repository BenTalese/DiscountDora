"""FU-211 — PreferredBuy CRUD on a stock item + detail exposure.

Free-text "what I actually buy" reminders (PROPOSAL_PRODUCTS_AS_OVERLAY §3.1).
Always available — not gated by the products or money features.
"""
import uuid

import requests

BASE = "http://localhost:5170/api"
STOCK_ITEMS = f"{BASE}/stock-items"


def _new_stock_item() -> str:
    level = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
    resp = requests.post(STOCK_ITEMS, json={
        "name": f"FU211-{uuid.uuid4().hex[:8]}",
        "stock_level_id": level,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["stock_item_id"]


def _preferred_buys(item_id: str) -> list:
    return requests.get(f"{STOCK_ITEMS}/{item_id}/detail").json()["preferred_buys"]


def test__preferred_buys__add_shows_on_detail(api):
    item = _new_stock_item()
    assert _preferred_buys(item) == []
    resp = requests.post(
        f"{STOCK_ITEMS}/{item}/preferred-buys", json={"label": "Vitasoy Oat Milky 1L"}
    )
    assert resp.status_code == 204, resp.text
    buys = _preferred_buys(item)
    assert len(buys) == 1
    assert buys[0]["label"] == "Vitasoy Oat Milky 1L"
    # FU-225: `position` column dropped — list is now sorted alphabetically
    # by the detail handler (see get_stock_item_detail.py:419). No `position`
    # field on the DTO.
    assert "position" not in buys[0]


def test__preferred_buys__rename_and_delete(api):
    item = _new_stock_item()
    requests.post(f"{STOCK_ITEMS}/{item}/preferred-buys", json={"label": "Original"})
    pb_id = _preferred_buys(item)[0]["preferred_buy_id"]

    renamed = requests.patch(
        f"{STOCK_ITEMS}/{item}/preferred-buys/{pb_id}", json={"label": "Renamed"}
    )
    assert renamed.status_code == 204, renamed.text
    assert _preferred_buys(item)[0]["label"] == "Renamed"

    deleted = requests.delete(f"{STOCK_ITEMS}/{item}/preferred-buys/{pb_id}")
    assert deleted.status_code == 204, deleted.text
    assert _preferred_buys(item) == []


def test__preferred_buys__detail_lists_alphabetically(api):
    """FU-225: the `/preferred-buys/reorder` endpoint was removed (manual
    reorder UI retired); the detail handler sorts by label.lower() instead."""
    item = _new_stock_item()
    for label in ("Charlie", "Alpha", "Bravo"):
        requests.post(f"{STOCK_ITEMS}/{item}/preferred-buys", json={"label": label})
    assert [b["label"] for b in _preferred_buys(item)] == ["Alpha", "Bravo", "Charlie"]


def test__preferred_buys__blank_label_rejected(api):
    item = _new_stock_item()
    resp = requests.post(f"{STOCK_ITEMS}/{item}/preferred-buys", json={"label": "   "})
    assert 400 <= resp.status_code < 500


def test__preferred_buys__wrong_item_scope_404(api):
    item_a = _new_stock_item()
    item_b = _new_stock_item()
    requests.post(f"{STOCK_ITEMS}/{item_a}/preferred-buys", json={"label": "Belongs to A"})
    pb_id = _preferred_buys(item_a)[0]["preferred_buy_id"]
    # Deleting A's preferred buy via B's scope must 404 (scoped lookup).
    resp = requests.delete(f"{STOCK_ITEMS}/{item_b}/preferred-buys/{pb_id}")
    assert resp.status_code == 404
