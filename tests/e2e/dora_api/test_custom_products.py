"""OD-2 — hand-entered ("custom") products.

`PreferredBuy` was supposed to cover shops no scraper reaches, but it is a
*label*: no price, no store, no history. So recording "the butcher's mince is
$12/kg" meant choosing between a note you couldn't compare and a product you
couldn't create.

The interesting tests here are the two isolation ones. A custom product is the
user's own figure, and the two ways it could be silently overwritten by
machinery are ingestion dedupe and the scheduled sync.
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"


def _store_name() -> str:
    return requests.get(f"{BASE}/stores").json()["items"][0]["name"]


def _create_custom(**overrides) -> str:
    body = {
        "name": f"Butcher Mince-{uuid4().hex[:8]}",
        "store_name": _store_name(),
        "brand": "Local Butcher",
        "is_active": True,
        "is_available": True,
        "price_now": 12.0,
        "size": "1kg",
        "size_unit": "KG",
        "size_value": 1.0,
    }
    body.update(overrides)
    resp = requests.post(f"{BASE}/products", json=body)
    assert resp.status_code == 201, resp.text
    return resp.headers["location"].rsplit(":", 1)[-1]


def _fetch(product_id: str) -> dict:
    items = requests.get(f"{BASE}/products").json()["items"]
    return next(p for p in items if p["product_id"] == product_id)


def test__a_manually_created_product_is_marked_custom():
    product_id = _create_custom()

    assert _fetch(product_id)["is_custom"] is True


def test__price_was_is_optional_and_defaults_to_no_markdown():
    """A hand-entered product usually has no "was" price. Defaulting to 0.0
    would make every custom product look permanently discounted."""
    product_id = _create_custom(price_now=12.0)

    product = _fetch(product_id)

    assert product["price_now"] == 12.0
    assert product["price_was"] == 12.0


def test__price_was_is_kept_when_supplied():
    product_id = _create_custom(price_now=9.0, price_was=12.0)

    product = _fetch(product_id)

    assert product["price_now"] == 9.0
    assert product["price_was"] == 12.0


def test__an_ingested_product_is_not_marked_custom():
    """Guards the marking: if `is_custom` were true for everything, the two
    isolation tests below would pass for the wrong reason."""
    items = requests.get(f"{BASE}/products").json()["items"]
    seeded = [p for p in items if not p["is_custom"]]

    assert seeded, "the seed should hold ingested (non-custom) products"


# ── Isolation: the two ways a custom product could be silently overwritten ──

def test__ingestion_does_not_adopt_a_custom_product_with_the_same_name():
    """Dedupe falls back to (store, name) for records without a stockcode, so
    a scraped "Mince" would otherwise match a hand-entered "Mince" at the same
    store and overwrite its brand, size and price — the user's own figure
    quietly replaced by scraped data."""
    store = _store_name()
    name = f"Contested Mince-{uuid4().hex[:8]}"
    custom_id = _create_custom(name=name, price_now=12.0, brand="Local Butcher")

    # A producer pushes a product of exactly the same name, same store.
    source = requests.post(f"{BASE}/ingestion-sources", json={
        "label": f"clash-{uuid4().hex[:6]}",
    }).json()
    key, source_id = source["key"], source["source"]["id"]
    external = f"Clash-{uuid4().hex[:6]}"
    push = {
        "products": [{
            "ref": "p0", "name": name, "store": external,
            "brand": "Supermarket Brand", "size": "500g",
            "size_unit": "G", "size_value": 500.0,
        }],
        "offers": [{
            "product_ref": "p0", "price_now": 3.0, "price_was": 4.0,
            "observed_at": "2026-09-08T00:00:00+00:00",
        }],
    }
    headers = {"Authorization": f"Bearer {key}", "Idempotency-Key": uuid4().hex}
    requests.post(f"{BASE}/ingest", headers=headers, json=push)
    store_id = next(
        s["store_id"] for s in requests.get(f"{BASE}/stores").json()["items"]
        if s["name"] == store
    )
    requests.put(
        f"{BASE}/ingestion-sources/{source_id}/store-mappings",
        json={"external_name": external, "store_id": store_id},
    )
    requests.post(f"{BASE}/ingest", headers={
        "Authorization": f"Bearer {key}", "Idempotency-Key": uuid4().hex,
    }, json=push)

    custom = _fetch(custom_id)
    assert custom["is_custom"] is True
    assert custom["price_now"] == 12.0, "the scrape overwrote the user's price"
    assert custom["brand"] == "Local Butcher", "the scrape overwrote the brand"


def test__the_sync_list_excludes_custom_products():
    """A custom product has no upstream to refresh from — offering it to a
    producer wastes a request at best, and has it matched against something
    else entirely at worst."""
    store = _store_name()
    name = f"Sync Excluded-{uuid4().hex[:8]}"
    _create_custom(name=name)

    source = requests.post(f"{BASE}/ingestion-sources", json={
        "label": f"sync-{uuid4().hex[:6]}",
    }).json()
    key, source_id = source["key"], source["source"]["id"]
    store_id = next(
        s["store_id"] for s in requests.get(f"{BASE}/stores").json()["items"]
        if s["name"] == store
    )
    requests.put(
        f"{BASE}/ingestion-sources/{source_id}/store-mappings",
        json={"external_name": store, "store_id": store_id},
    )

    listed = requests.get(
        f"{BASE}/ingest/products", headers={"Authorization": f"Bearer {key}"},
    ).json()["items"]

    assert all(row["name"] != name for row in listed)


def test__the_sync_list_still_offers_ingested_products():
    """Guards the test above — if the list were simply empty, it would pass
    without the exclusion doing anything."""
    source = requests.post(f"{BASE}/ingestion-sources", json={
        "label": f"sync2-{uuid4().hex[:6]}",
    }).json()
    key, source_id = source["key"], source["source"]["id"]
    stores = requests.get(f"{BASE}/stores").json()["items"]
    for store in stores:
        requests.put(
            f"{BASE}/ingestion-sources/{source_id}/store-mappings",
            json={"external_name": store["name"], "store_id": store["store_id"]},
        )

    listed = requests.get(
        f"{BASE}/ingest/products", headers={"Authorization": f"Bearer {key}"},
    ).json()["items"]

    assert listed, "no ingested products offered — the exclusion is too broad"
