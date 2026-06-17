"""C-10.2 / C-10.3 — admin CRUD over IngestionStoreMapping.

The API access page's per-source store-mappings panel consumes these
endpoints; the ingest flow auto-creates quarantined rows on first
sighting of an unknown external name.
"""
import uuid

import requests

BASE = "http://localhost:5170/api"
SOURCES = f"{BASE}/ingestion-sources"


def _mint() -> tuple[str, str]:
    body = requests.post(SOURCES, json={"label": f"src-{uuid.uuid4().hex[:8]}"}).json()
    return body["source"]["id"], body["key"]


def _seeded_merchant_id() -> str:
    return requests.get(f"{BASE}/merchants").json()["items"][0]["merchant_id"]


def test__store_mappings__list_starts_empty(api):
    sid, _ = _mint()
    items = requests.get(f"{SOURCES}/{sid}/store-mappings").json()["items"]
    assert items == []


def test__store_mappings__upsert_then_list(api):
    sid, _ = _mint()
    mid = _seeded_merchant_id()
    name = f"ExternalCo-{uuid.uuid4().hex[:6]}"

    resp = requests.put(f"{SOURCES}/{sid}/store-mappings", json={
        "external_name": name, "merchant_id": mid,
    })
    assert resp.status_code == 200, resp.text
    assert resp.json()["merchant_id"] == mid
    assert resp.json()["external_name"] == name

    items = requests.get(f"{SOURCES}/{sid}/store-mappings").json()["items"]
    assert any(m["external_name"] == name and m["merchant_id"] == mid for m in items)


def test__store_mappings__quarantine_via_null_merchant(api):
    sid, _ = _mint()
    name = f"PendingCo-{uuid.uuid4().hex[:6]}"
    resp = requests.put(f"{SOURCES}/{sid}/store-mappings", json={
        "external_name": name, "merchant_id": None,
    })
    assert resp.status_code == 200, resp.text
    assert resp.json()["merchant_id"] is None
    assert resp.json()["merchant_name"] is None


def test__store_mappings__bad_merchant_id_rejected(api):
    sid, _ = _mint()
    resp = requests.put(f"{SOURCES}/{sid}/store-mappings", json={
        "external_name": "X",
        "merchant_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 400, resp.text


def test__store_mappings__delete(api):
    sid, _ = _mint()
    mid = _seeded_merchant_id()
    created = requests.put(f"{SOURCES}/{sid}/store-mappings", json={
        "external_name": f"DropMe-{uuid.uuid4().hex[:6]}",
        "merchant_id": mid,
    }).json()

    resp = requests.delete(f"{SOURCES}/{sid}/store-mappings/{created['id']}")
    assert resp.status_code == 204, resp.text
    items = requests.get(f"{SOURCES}/{sid}/store-mappings").json()["items"]
    assert all(m["id"] != created["id"] for m in items)


def test__store_mappings__unknown_source_404(api):
    bogus = str(uuid.uuid4())
    assert requests.get(f"{SOURCES}/{bogus}/store-mappings").status_code == 404
    assert requests.put(
        f"{SOURCES}/{bogus}/store-mappings",
        json={"external_name": "x", "merchant_id": None},
    ).status_code == 404
