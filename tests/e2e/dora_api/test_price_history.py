"""End-to-end coverage for the N8 Price History Explorer endpoints."""
import uuid

import requests


BASE = "http://localhost:5170/api/price-history"


def test__price_history__missing_product_ids__is_400(api):
    response = requests.get(BASE)
    assert response.status_code == 400


def test__price_history__too_many_product_ids__is_400(api):
    ids = ",".join(str(uuid.uuid4()) for _ in range(6))
    response = requests.get(f"{BASE}?product_ids={ids}")
    assert response.status_code == 400


def test__price_history__unknown_product__returns_placeholder(api):
    bogus = uuid.uuid4()
    response = requests.get(f"{BASE}?product_ids={bogus}&range=30d")
    assert response.status_code == 200
    series = response.json()["series"]
    assert len(series) == 1
    assert series[0]["product_id"] == str(bogus)
    assert series[0]["points"] == []
    assert series[0]["name"] == "(unknown)"


def test__price_alerts__crud_round_trip(api):
    # Pick any existing product from the search API or skip when none.
    products = requests.get("http://localhost:5170/api/products").json().get("items") or []
    if not products:
        return
    product_id = products[0]["product_id"]

    # Create
    create = requests.post(f"{BASE}/alerts", json={
        "product_id": product_id, "threshold_unit_price": 1.23,
    })
    assert create.status_code == 200, create.text
    alert_id = create.json()["price_alert_id"]

    # List
    listed = requests.get(f"{BASE}/alerts").json()["items"]
    assert any(a["price_alert_id"] == alert_id for a in listed)

    # Delete
    deleted = requests.delete(f"{BASE}/alerts/{alert_id}")
    assert deleted.status_code == 204

    # Subsequent delete → 404
    redel = requests.delete(f"{BASE}/alerts/{alert_id}")
    assert redel.status_code == 404


def test__price_alerts__create_for_unknown_product__is_404(api):
    response = requests.post(f"{BASE}/alerts", json={
        "product_id": str(uuid.uuid4()), "threshold_unit_price": 5.0,
    })
    assert response.status_code == 404


def test__price_alerts__zero_threshold__is_422(api):
    products = requests.get("http://localhost:5170/api/products").json().get("items") or []
    if not products:
        return
    response = requests.post(f"{BASE}/alerts", json={
        "product_id": products[0]["product_id"], "threshold_unit_price": 0,
    })
    # Pydantic gt=0 → 400/422 via the middleware.
    assert response.status_code in (400, 422)
