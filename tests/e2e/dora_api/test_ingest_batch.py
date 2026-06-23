"""C-10.2 — `POST /api/ingest` (PROPOSAL_INGESTION_API §2.2-§2.4 + FU-190).

Covers the producer-facing contract:
- bearer-auth (good, missing, bad, disabled key)
- products dedupe (stockcode-first, name fallback) — shared catalogue
- offers append-only with the dedupe key
- per-record result DTO (a bad record never fails the batch)
- Idempotency-Key replay = no-op
- FU-190: unknown merchant quarantines into IngestionStoreMapping;
  mapping it then unblocks future ingest for that name.
- FU-232: multipack `pack_count` round-trips onto the Product row.
"""
import uuid

import requests

from dora_api.app import app
from dora_api.domain.entities.product import Product
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

BASE = "http://localhost:5170/api"
INGEST = f"{BASE}/ingest"
SOURCES = f"{BASE}/ingestion-sources"


def _mint_key(label: str | None = None) -> tuple[str, str]:
    """Returns (source_id, raw_key)."""
    payload = {"label": label or f"src-{uuid.uuid4().hex[:8]}"}
    resp = requests.post(SOURCES, json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return body["source"]["id"], body["key"]


def _post_ingest(key: str, body: dict, idem: str | None = None) -> requests.Response:
    headers = {"Authorization": f"Bearer {key}"}
    if idem is not None:
        headers["Idempotency-Key"] = idem
    return requests.post(INGEST, json=body, headers=headers)


def _seeded_store_id() -> str:
    """Reuse a seeded Store — the test DB is session-scoped and other
    tests assert on the seeded store total, so we must not pollute."""
    stores = requests.get(f"{BASE}/stores").json()["items"]
    assert stores, "expected seed to provision at least one store"
    return stores[0]["store_id"]


def _map_store(source_id: str, external_name: str, store_id: str) -> None:
    """C-10.3 admin route — used here to satisfy FU-190 before pushing
    real records. Defined in C-10.3 (ingestion_source_admin)."""
    resp = requests.put(
        f"{SOURCES}/{source_id}/store-mappings",
        json={"external_name": external_name, "store_id": store_id},
    )
    assert resp.status_code in (200, 201, 204), resp.text


def test__ingest__rejects_missing_bearer(api):
    resp = requests.post(INGEST, json={"products": []})
    assert resp.status_code == 401, resp.text


def test__ingest__rejects_bad_bearer(api):
    resp = requests.post(INGEST, json={"products": []},
                         headers={"Authorization": "Bearer not-a-real-key"})
    assert resp.status_code == 401, resp.text


def test__ingest__rejects_disabled_key(api):
    sid, key = _mint_key()
    requests.patch(f"{SOURCES}/{sid}", json={"enabled": False})
    resp = _post_ingest(key, {"products": []})
    assert resp.status_code == 401, resp.text


def test__ingest__unknown_store_quarantines(api):
    """FU-190 — an unknown merchant name does NOT auto-create. The
    product record is skipped with `store_not_mapped`."""
    _sid, key = _mint_key()
    body = {
        "products": [{
            "ref": "p1",
            "name": "Brand X Oat Milk 1L",
            "store": "MysteryStore",
            "merchant_stockcode": "ABC123",
        }],
    }
    resp = _post_ingest(key, body)
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["skipped"] and result["skipped"][0]["reason"] == "store_not_mapped"
    assert not result["accepted"]


def test__ingest__roundtrip_after_store_mapping(api):
    """Map the store, push a product + offer, observe it appended."""
    sid, key = _mint_key()
    store_id = _seeded_store_id()
    _map_store(sid, "ExternalStoreName", store_id)

    body = {
        "products": [{
            "ref": "p1",
            "name": f"Brand X Oat Milk {uuid.uuid4().hex[:6]}",
            "store": "ExternalStoreName",
            "merchant_stockcode": uuid.uuid4().hex[:10],
        }],
        "offers": [{
            "product_ref": "p1",
            "price_now": 4.50,
            "price_was": 5.00,
            "observed_at": "2026-06-17T10:00:00+00:00",
        }],
    }
    resp = _post_ingest(key, body)
    assert resp.status_code == 200, resp.text
    result = resp.json()
    accepted_kinds = sorted(r["kind"] for r in result["accepted"])
    assert accepted_kinds == ["offer", "product"], result


def test__ingest__product_dedupe_by_stockcode_then_offer_appends(api):
    """Re-push the same product (same stockcode) → it dedupes; the
    new offer appends a new historic point."""
    sid, key = _mint_key()
    store_id = _seeded_store_id()
    _map_store(sid, "ExternalStore", store_id)
    stockcode = uuid.uuid4().hex[:10]

    first = _post_ingest(key, {
        "products": [{
            "ref": "p1",
            "name": "Same Product",
            "store": "ExternalStore",
            "merchant_stockcode": stockcode,
        }],
        "offers": [{
            "product_ref": "p1",
            "price_now": 3.00,
            "observed_at": "2026-06-17T10:00:00+00:00",
        }],
    })
    assert first.status_code == 200, first.text

    second = _post_ingest(key, {
        "products": [{
            "ref": "p1",
            "name": "Same Product",
            "store": "ExternalStore",
            "merchant_stockcode": stockcode,
        }],
        "offers": [{
            "product_ref": "p1",
            "price_now": 2.50,
            "observed_at": "2026-06-17T11:00:00+00:00",
        }],
    })
    assert second.status_code == 200, second.text
    result = second.json()
    # Product row is "updated" not "created" on the resend.
    product_acks = [r for r in result["accepted"] if r["kind"] == "product"]
    assert product_acks and "updated" in (product_acks[0].get("note") or "")
    # New offer accepted (different observed_at + price).
    offer_acks = [r for r in result["accepted"] if r["kind"] == "offer"]
    assert offer_acks, result


def test__ingest__duplicate_offer_skipped(api):
    """Same (product, observed_at, price_now) twice → second is
    deduped as `duplicate`, not appended."""
    sid, key = _mint_key()
    store_id = _seeded_store_id()
    _map_store(sid, "ExternalStore", store_id)

    stockcode = uuid.uuid4().hex[:10]
    base = {
        "products": [{
            "ref": "p1",
            "name": "Dup Test",
            "store": "ExternalStore",
            "merchant_stockcode": stockcode,
        }],
        "offers": [{
            "product_ref": "p1",
            "price_now": 9.99,
            "observed_at": "2026-06-17T12:00:00+00:00",
        }],
    }
    first = _post_ingest(key, base)
    assert first.status_code == 200, first.text

    second = _post_ingest(key, base)
    assert second.status_code == 200, second.text
    skipped = [r for r in second.json()["skipped"] if r["kind"] == "offer"]
    assert skipped and skipped[0]["reason"] == "duplicate"


def test__ingest__idempotency_key_replays_to_noop(api):
    sid, key = _mint_key()
    store_id = _seeded_store_id()
    _map_store(sid, "ExternalStore", store_id)
    idem = uuid.uuid4().hex

    body = {
        "products": [{
            "ref": "p1",
            "name": "Idem Test",
            "store": "ExternalStore",
            "merchant_stockcode": uuid.uuid4().hex[:10],
        }],
        "offers": [{
            "product_ref": "p1",
            "price_now": 1.00,
            "observed_at": "2026-06-17T13:00:00+00:00",
        }],
    }
    first = _post_ingest(key, body, idem=idem)
    assert first.status_code == 200, first.text
    assert first.json()["idempotent_replay"] is False
    assert len(first.json()["accepted"]) == 2

    second = _post_ingest(key, body, idem=idem)
    assert second.status_code == 200, second.text
    assert second.json()["idempotent_replay"] is True
    assert second.json()["accepted"] == []
    assert second.json()["skipped"] == []


def test__ingest__bad_record_does_not_fail_batch(api):
    """A bad record returns per-record `failed`, not a 4xx."""
    sid, key = _mint_key()
    store_id = _seeded_store_id()
    _map_store(sid, "ExternalStore", store_id)

    body = {
        "products": [{
            "ref": "p1",
            "name": "Good Product",
            "store": "ExternalStore",
            "merchant_stockcode": uuid.uuid4().hex[:10],
        }],
        "offers": [
            {
                "product_ref": "p1",
                "price_now": 2.00,
                "observed_at": "2026-06-17T10:00:00+00:00",
            },
            {
                "product_ref": "p-does-not-exist",
                "price_now": 3.00,
                "observed_at": "2026-06-17T10:00:00+00:00",
            },
        ],
    }
    resp = _post_ingest(key, body)
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert any(r["kind"] == "product" for r in result["accepted"])
    assert any(r["kind"] == "offer" for r in result["accepted"])
    assert any(
        r["kind"] == "offer" and r["reason"] == "product_unknown"
        for r in result["failed"]
    ), result


def test__ingest__pack_count_round_trips_on_product(api):
    """FU-232 — the multipack `pack_count` column (schema added with the
    FU-227 follow-up) is now accepted on `_ProductIn` and persisted on
    `Product.pack_count`. Re-pushing the same product with a different
    `pack_count` updates the row (additive: a NULL push doesn't clobber
    an existing value, matching the other `or existing.*` fields)."""
    sid, key = _mint_key()
    store_id = _seeded_store_id()
    _map_store(sid, "MultipackStore", store_id)

    stockcode = uuid.uuid4().hex[:10]
    name = f"Activia 4-pack {uuid.uuid4().hex[:6]}"
    body = {
        "products": [{
            "ref": "p1",
            "name": name,
            "store": "MultipackStore",
            "merchant_stockcode": stockcode,
            "size_value": 500.0,    # total across the bundle
            "size_unit": "g",
            "pack_count": 4,
        }],
    }
    resp = _post_ingest(key, body)
    assert resp.status_code == 200, resp.text
    assert resp.json()["accepted"][0]["kind"] == "product", resp.text

    with app.app_context():
        repo = SqlAlchemyRepository()
        stockcode_field = EntityField(Product, Product.Fields.MERCHANT_STOCKCODE)
        rows = repo.get(Product).all(stockcode_field.eq(stockcode))
        assert len(rows) == 1, rows
        assert rows[0].pack_count == 4
        assert rows[0].size_value == 500.0

    # Push the same product again with no pack_count — the existing
    # value sticks (matches `existing.pack_count or existing.pack_count`).
    body_no_pack = {
        "products": [{
            "ref": "p1",
            "name": name,
            "store": "MultipackStore",
            "merchant_stockcode": stockcode,
        }],
    }
    resp = _post_ingest(key, body_no_pack)
    assert resp.status_code == 200, resp.text
    with app.app_context():
        repo = SqlAlchemyRepository()
        stockcode_field = EntityField(Product, Product.Fields.MERCHANT_STOCKCODE)
        rows = repo.get(Product).all(stockcode_field.eq(stockcode))
        assert rows[0].pack_count == 4

    # And rejects a non-positive pack_count (Field(gt=0)).
    body_bad = {
        "products": [{
            "ref": "p1",
            "name": f"bad {uuid.uuid4().hex[:6]}",
            "store": "MultipackStore",
            "pack_count": 0,
        }],
    }
    resp = _post_ingest(key, body_bad)
    assert resp.status_code == 400, resp.text


def test__ingest__rejects_price_observations_field(api):
    """FU-227 chunk 7 (J1) — observations are in-app input only; the producer
    path was removed. A payload still sending `price_observations[]` is
    rejected by `extra="forbid"` (400) before any record is processed. This
    pins the contract removal so a future agent can't quietly re-add the
    field without revisiting Idea A."""
    _, key = _mint_key()
    body = {
        "products": [],
        "offers": [],
        "price_observations": [{
            "product_ref": "p1",
            "price": 1.00,
            "observed_at": "2026-06-17T10:00:00+00:00",
        }],
    }
    resp = _post_ingest(key, body)
    assert resp.status_code == 400, resp.text
    detail = (resp.json().get("errors") or "") + (resp.json().get("detail") or "")
    assert "price_observations" in detail.lower() or "extra" in detail.lower(), resp.text
