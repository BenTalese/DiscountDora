"""FU-213 — StockItemPriceObservation: log "what this cost me" + derived unit cost.

The user logs the TOTAL price + qty + unit; the server derives the per-unit cost
(R-003 — the client never divides). PROPOSAL_PRODUCTS_AS_OVERLAY §3.2.
"""
import uuid

import requests

BASE = "http://localhost:5170/api"
STOCK_ITEMS = f"{BASE}/stock-items"


def _new_stock_item() -> str:
    level = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
    resp = requests.post(STOCK_ITEMS, json={
        "name": f"FU213-{uuid.uuid4().hex[:8]}",
        "stock_level_id": level,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["stock_item_id"]


def _detail(item_id: str) -> dict:
    return requests.get(f"{STOCK_ITEMS}/{item_id}/detail").json()


def test__price_observation__add_derives_unit_cost(api):
    item = _new_stock_item()
    d = _detail(item)
    assert d["price_observations"] == []
    assert d["unit_cost"] is None

    resp = requests.post(
        f"{STOCK_ITEMS}/{item}/price-observations",
        json={"price": 6.0, "qty": 2.0, "unit": "L"},
    )
    assert resp.status_code == 204, resp.text
    d = _detail(item)
    assert len(d["price_observations"]) == 1
    obs = d["price_observations"][0]
    assert obs["price"] == 6.0 and obs["qty"] == 2.0 and obs["unit"] == "L"
    assert obs["source"] == "manual"
    # Server derives per-unit cost (6 / 2 = 3) — the client never divides.
    assert d["unit_cost"] == 3.0


def test__price_observation__latest_wins_for_unit_cost(api):
    item = _new_stock_item()
    requests.post(f"{STOCK_ITEMS}/{item}/price-observations", json={
        "price": 10.0, "qty": 1.0, "unit": "L", "observed_at": "2026-01-01T00:00:00+00:00",
    })
    requests.post(f"{STOCK_ITEMS}/{item}/price-observations", json={
        "price": 6.0, "qty": 2.0, "unit": "L", "observed_at": "2026-06-01T00:00:00+00:00",
    })
    d = _detail(item)
    assert len(d["price_observations"]) == 2
    # unit_cost comes from the most recent observation (3.0), not the older 10.0.
    assert d["unit_cost"] == 3.0


def test__price_observation__delete_clears_unit_cost(api):
    item = _new_stock_item()
    requests.post(
        f"{STOCK_ITEMS}/{item}/price-observations",
        json={"price": 5.0, "qty": 1.0, "unit": "ea"},
    )
    obs_id = _detail(item)["price_observations"][0]["observation_id"]
    resp = requests.delete(f"{STOCK_ITEMS}/{item}/price-observations/{obs_id}")
    assert resp.status_code == 204, resp.text
    d = _detail(item)
    assert d["price_observations"] == []
    assert d["unit_cost"] is None


def test__price_observation__non_positive_rejected(api):
    item = _new_stock_item()
    resp = requests.post(
        f"{STOCK_ITEMS}/{item}/price-observations",
        json={"price": 0, "qty": 1, "unit": "L"},
    )
    assert 400 <= resp.status_code < 500
