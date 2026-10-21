"""Verify-campaign Batch 3 — Zero-Input Pantry HTTP seam (P8-07).

The belief *engine* (bands, cook drift, override-wins, thin-history caution,
differs flag) is unit-pinned in `tests/test_pantry_belief.py`. What had no
test was the HTTP layer around it:

  - GET /api/stock-items/beliefs — response shape, and the per-user
    `inferred_pantry_enabled` gate short-circuiting to
    `{enabled: false, beliefs: {}}` (DORA_VERIFY's "inference OFF" check).
  - The Preferences → Pantry toggle persisting through PATCH /api/auth/me
    (server truth for "flipping it persists across reload").
  - The recorded-level pin end-to-end: a fresh level change reads back from
    the endpoint as that band at HIGH confidence (override wins).
"""
from uuid import uuid4

import pytest
import requests

from dora_api.domain.stock_status import LOW_STOCK_SEQUENCE

BASE = "http://localhost:5170/api"
BELIEFS = f"{BASE}/stock-items/beliefs"
ME = f"{BASE}/auth/me"

BELIEF_KEYS = {"believed_band", "confidence_band", "reason"}


@pytest.fixture
def levels_by_sequence(api):
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return {l["sequence"]: l["stock_level_id"] for l in levels}


def test__beliefs__default_on__returns_enabled_with_belief_map(api):
    resp = requests.get(BELIEFS)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["enabled"] is True
    # The seed has stock items, so the map is populated; every entry carries
    # the explainable-belief contract the SPA chips render from.
    assert body["beliefs"], "expected beliefs for the seeded pantry"
    for item_id, belief in body["beliefs"].items():
        assert BELIEF_KEYS <= set(belief.keys()), (item_id, belief)
        assert belief["believed_band"] in ("out", "low", "stocked")
        assert belief["confidence_band"] in ("high", "medium", "low")
        assert belief["reason"]


def test__beliefs__per_user_opt_out__gates_and_persists(api):
    # Flip inference off via the same PATCH the Preferences → Pantry toggle
    # rides; the endpoint must short-circuit and the flag must persist.
    off = requests.patch(ME, json={"inferred_pantry_enabled": False})
    assert off.status_code in (200, 204), off.text

    assert requests.get(ME).json()["inferred_pantry_enabled"] is False
    assert requests.get(BELIEFS).json() == {"enabled": False, "beliefs": {}}

    on = requests.patch(ME, json={"inferred_pantry_enabled": True})
    assert on.status_code in (200, 204), on.text
    assert requests.get(ME).json()["inferred_pantry_enabled"] is True
    body = requests.get(BELIEFS).json()
    assert body["enabled"] is True and body["beliefs"]


def test__beliefs__fresh_level_change_pins_recorded_band_high_confidence(
    levels_by_sequence, api
):
    # Override-wins, end-to-end: PATCHing a level counts as a fresh check
    # (bumps last_checked_at), so the belief must read back as the recorded
    # band at HIGH confidence with no "differs" flag.
    resp = requests.post(f"{BASE}/stock-items", json={
        "name": f"belief-pin-{uuid4()}",
        "stock_level_id": levels_by_sequence[0],
    })
    assert resp.status_code == 201, resp.text
    item_id = resp.json()["stock_item_id"]

    patched = requests.patch(f"{BASE}/stock-items/{item_id}", json={
        "stock_level_id": levels_by_sequence[LOW_STOCK_SEQUENCE],
    })
    assert patched.status_code in (200, 204), patched.text

    belief = requests.get(BELIEFS).json()["beliefs"].get(item_id)
    assert belief is not None, "freshly-checked item should carry a belief"
    assert belief["believed_band"] == "low"
    assert belief["confidence_band"] == "high"
    assert belief.get("differs_from_recorded") in (False, None)
