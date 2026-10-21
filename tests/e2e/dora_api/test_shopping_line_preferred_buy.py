"""FU-215 — ShoppingListLine.preferred_buy_id hint.

A shopping line for a stock item that has PreferredBuy labels can carry one of
them as a hint. PROPOSAL_PRODUCTS_AS_OVERLAY §3.1.
"""
import uuid

import requests

BASE = "http://localhost:5170/api"
STOCK_ITEMS = f"{BASE}/stock-items"
SHOPPING_LISTS = f"{BASE}/shopping-lists"


def _new_stock_item_with_buy(label: str):
    level = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
    item = requests.post(STOCK_ITEMS, json={
        "name": f"FU215-{uuid.uuid4().hex[:8]}", "stock_level_id": level,
    }).json()["stock_item_id"]
    assert requests.post(
        f"{STOCK_ITEMS}/{item}/preferred-buys", json={"label": label}
    ).status_code == 204
    pb_id = (
        requests.get(f"{STOCK_ITEMS}/{item}/detail").json()["preferred_buys"][0]["preferred_buy_id"]
    )
    return item, pb_id


def _list_with_line(item_id: str):
    list_id = requests.post(
        SHOPPING_LISTS, json={"name": f"FU215-{uuid.uuid4().hex[:8]}"}
    ).json()["shopping_list_id"]
    assert requests.post(
        f"{SHOPPING_LISTS}/{list_id}/lines", json={"stock_item_id": item_id}
    ).status_code in (200, 201)
    line_id = requests.get(f"{SHOPPING_LISTS}/{list_id}").json()["lines"][0]["line_id"]
    return list_id, line_id


def _line(list_id: str) -> dict:
    return requests.get(f"{SHOPPING_LISTS}/{list_id}").json()["lines"][0]


def test__line_preferred_buy__detail_exposes_item_labels(api):
    item, _ = _new_stock_item_with_buy("Vitasoy Oat Milky 1L")
    list_id, _ = _list_with_line(item)
    line = _line(list_id)
    assert "Vitasoy Oat Milky 1L" in [pb["label"] for pb in line["preferred_buys"]]
    assert line["preferred_buy_id"] is None


def test__line_preferred_buy__set_and_clear(api):
    item, pb_id = _new_stock_item_with_buy("Brand X 500g")
    list_id, line_id = _list_with_line(item)

    set_resp = requests.patch(
        f"{SHOPPING_LISTS}/{list_id}/lines/{line_id}", json={"preferred_buy_id": pb_id}
    )
    assert set_resp.status_code == 204, set_resp.text
    assert _line(list_id)["preferred_buy_id"] == pb_id

    clear_resp = requests.patch(
        f"{SHOPPING_LISTS}/{list_id}/lines/{line_id}", json={"clear_preferred_buy": True}
    )
    assert clear_resp.status_code == 204, clear_resp.text
    assert _line(list_id)["preferred_buy_id"] is None
