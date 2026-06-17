"""C-10.2 — `POST /api/ingest` (PROPOSAL_INGESTION_API §2.2-§2.4 + FU-190).

Covers the producer-facing contract:
- bearer-auth (good, missing, bad, disabled key)
- products dedupe (stockcode-first, name fallback) — shared catalogue
- offers append-only with the dedupe key
- per-record result DTO (a bad record never fails the batch)
- Idempotency-Key replay = no-op
- FU-190: unknown merchant quarantines into IngestionStoreMapping;
  mapping it then unblocks future ingest for that name.
"""
import uuid

import requests

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


def _seeded_merchant_id() -> str:
    """Reuse a seeded Merchant — the test DB is session-scoped and other
    tests assert on the seeded merchant total, so we must not pollute."""
    merchants = requests.get(f"{BASE}/merchants").json()["items"]
    assert merchants, "expected seed to provision at least one merchant"
    return merchants[0]["merchant_id"]


def _map_store(source_id: str, external_name: str, merchant_id: str) -> None:
    """C-10.3 admin route — used here to satisfy FU-190 before pushing
    real records. Defined in C-10.3 (ingestion_source_admin)."""
    resp = requests.put(
        f"{SOURCES}/{source_id}/store-mappings",
        json={"external_name": external_name, "merchant_id": merchant_id},
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
            "merchant": "MysteryStore",
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
    merchant_id = _seeded_merchant_id()
    _map_store(sid, "ExternalStoreName", merchant_id)

    body = {
        "products": [{
            "ref": "p1",
            "name": f"Brand X Oat Milk {uuid.uuid4().hex[:6]}",
            "merchant": "ExternalStoreName",
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
    merchant_id = _seeded_merchant_id()
    _map_store(sid, "ExternalStore", merchant_id)
    stockcode = uuid.uuid4().hex[:10]

    first = _post_ingest(key, {
        "products": [{
            "ref": "p1",
            "name": "Same Product",
            "merchant": "ExternalStore",
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
            "merchant": "ExternalStore",
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
    merchant_id = _seeded_merchant_id()
    _map_store(sid, "ExternalStore", merchant_id)

    stockcode = uuid.uuid4().hex[:10]
    base = {
        "products": [{
            "ref": "p1",
            "name": "Dup Test",
            "merchant": "ExternalStore",
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
    merchant_id = _seeded_merchant_id()
    _map_store(sid, "ExternalStore", merchant_id)
    idem = uuid.uuid4().hex

    body = {
        "products": [{
            "ref": "p1",
            "name": "Idem Test",
            "merchant": "ExternalStore",
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
    merchant_id = _seeded_merchant_id()
    _map_store(sid, "ExternalStore", merchant_id)

    body = {
        "products": [{
            "ref": "p1",
            "name": "Good Product",
            "merchant": "ExternalStore",
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
