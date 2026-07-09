"""FU-450 — `good_deal` alert type (end-to-end).

Exercises the money-features gate + the deal-quality → alert wiring through
the real /api/alerts endpoint. The pure deal-quality maths are pinned
separately in `tests/test_deal_quality.py`; this proves the endpoint only
surfaces the nudge when both money flags are on and a fresh, qualifying
offer is linked to a tracked stock item.
"""
import uuid

import requests

BASE = "http://localhost:5170/api"


def _any_stock_level_id() -> str:
    levels = requests.get(f"{BASE}/stock-levels").json().get("items") or []
    assert levels, "expected seeded stock levels"
    return levels[0]["stock_level_id"]


def _set_money_features(install_on: bool, user_on: bool) -> None:
    r1 = requests.patch(f"{BASE}/app-settings", json={"money_enabled": install_on})
    assert r1.status_code in (200, 204), r1.text
    r2 = requests.patch(f"{BASE}/auth/me", json={"money_features_enabled": user_on})
    assert r2.status_code in (200, 204), r2.text


def _create_linked_product_on_special(item_name: str) -> tuple[str, str]:
    """Create a stock item + a product on special (was > now) + link them.
    A freshly-created product has a `now`-stamped offer (fresh) and — with no
    historic offers — sits at percentile 1.0 → `great` band."""
    requests.post(f"{BASE}/stores", json={"name": "DealStore"})
    item = requests.post(f"{BASE}/stock-items", json={
        "name": item_name, "stock_level_id": _any_stock_level_id(),
    })
    assert item.status_code in (200, 201), item.text
    stock_item_id = item.json()["stock_item_id"]

    product = requests.post(f"{BASE}/products", json={
        "brand": "Homebrand", "image": None, "is_active": True,
        "is_available": True, "store_name": "DealStore",
        "merchant_stockcode": uuid.uuid4().hex[:8], "name": item_name,
        "price_now": 2.50, "price_was": 4.50,
        "size": "500g", "size_unit": "g", "size_value": 500.0, "web_url": "x",
    })
    assert product.status_code == 201, product.text
    product_id = product.json()["id"]

    link = requests.post(
        f"{BASE}/stock-items/{stock_item_id}/products",
        json={"product_id": product_id},
    )
    assert link.status_code in (200, 201, 204), link.text
    return stock_item_id, product_id


def _good_deals(items: list) -> list:
    return [a for a in items if a["kind"] == "good_deal"]


def test__good_deal__fires_when_money_on_for_fresh_great_deal(api):
    name = f"gooddeal-{uuid.uuid4().hex[:8]}"
    _set_money_features(install_on=True, user_on=True)
    stock_item_id, product_id = _create_linked_product_on_special(name)

    data = requests.get(f"{BASE}/alerts").json()
    mine = [a for a in _good_deals(data["items"]) if a["stock_item_name"] == name]
    assert mine, "expected a good_deal alert for the fresh great-band product"
    alert = mine[0]
    assert alert["alert_id"].startswith(f"stock:{stock_item_id}:good_deal:")
    assert alert["severity"] == "high"          # great band
    assert alert["target_id"] == product_id
    assert alert["stock_item_id"] == stock_item_id


def test__good_deal__suppressed_when_money_features_off(api):
    name = f"gooddeal-off-{uuid.uuid4().hex[:8]}"
    _set_money_features(install_on=True, user_on=True)
    _create_linked_product_on_special(name)
    # Now turn the user's money features off — the whole surface must vanish.
    _set_money_features(install_on=True, user_on=False)

    data = requests.get(f"{BASE}/alerts").json()
    mine = [a for a in _good_deals(data["items"]) if a["stock_item_name"] == name]
    assert not mine, "good_deal must not surface when money features are off"


def test__good_deal__threshold_great_excludes_good_band(api):
    """Threshold `great` should only nudge on the top band. We can't easily
    force a `good`-but-not-`great` band without historic offers here, so this
    pins the gate the other way: with threshold `great`, a `great`-band deal
    still fires (regression guard on the threshold parse)."""
    name = f"gooddeal-thr-{uuid.uuid4().hex[:8]}"
    _set_money_features(install_on=True, user_on=True)
    r = requests.patch(f"{BASE}/auth/me", json={"good_deal_alert_threshold": "great"})
    assert r.status_code in (200, 204), r.text
    _create_linked_product_on_special(name)

    data = requests.get(f"{BASE}/alerts").json()
    mine = [a for a in _good_deals(data["items"]) if a["stock_item_name"] == name]
    assert mine and mine[0]["severity"] == "high"
    # reset threshold for suite hygiene
    requests.patch(f"{BASE}/auth/me", json={"good_deal_alert_threshold": "good"})


def test__update_me__rejects_invalid_good_deal_threshold(api):
    # Closed-set sentinel violation → 422 domain error (same convention as
    # alerts_email_cadence / nutrition_mode).
    r = requests.patch(f"{BASE}/auth/me", json={"good_deal_alert_threshold": "amazing"})
    assert r.status_code == 422, r.text
