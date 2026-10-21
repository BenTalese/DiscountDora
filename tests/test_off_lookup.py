"""P8-02 — Open Food Facts lookup unit tests.

The endpoint's real network call is monkeypatched so tests exercise the
parser, cache, and fallback branches without hitting OFF. E2E coverage
(scanning-off gating, plumbing through the SPA scan flow) is a
browser-verify item — see `DORA_VERIFY.md`.
"""
from dora_api.features.data import off_lookup


def _reset_cache():
    off_lookup._CACHE.clear()


def _fake_off_hit(**overrides) -> dict:
    """Shape mirrors what `_parse_off_response` returns for a valid OFF
    product document."""
    base = {
        "found": True,
        "name": "Vitasoy Oat Milky 1L",
        "brand": "Vitasoy",
        "image_url": "https://images.openfoodfacts.org/vitasoy.jpg",
        "categories": "Beverages, Plant-based beverages",
        "quantity": "1 L",
    }
    base.update(overrides)
    return base


def test__parse_off_response__status_zero__returns_not_found():
    result = off_lookup._parse_off_response({"status": 0})
    assert result == {"found": False}


def test__parse_off_response__hit__extracts_expected_fields():
    result = off_lookup._parse_off_response({
        "status": 1,
        "product": {
            "product_name": "Corn Flakes",
            "brands": "Kellogg's",
            "image_front_url": "https://images.openfoodfacts.org/cf.jpg",
            "categories": "Breakfasts, Cereals",
            "quantity": "500 g",
        },
    })
    assert result["found"] is True
    assert result["name"] == "Corn Flakes"
    assert result["brand"] == "Kellogg's"
    assert result["image_url"] == "https://images.openfoodfacts.org/cf.jpg"
    assert result["categories"] == "Breakfasts, Cereals"
    assert result["quantity"] == "500 g"


def test__parse_off_response__falls_back_to_generic_name_and_image_url():
    """OFF sometimes leaves `product_name` empty but provides
    `generic_name`; same story for `image_front_url` vs the generic
    `image_url`. Both should be picked up so the SPA sees a suggestion."""
    result = off_lookup._parse_off_response({
        "status": 1,
        "product": {
            "product_name": "  ",
            "generic_name": "Rolled Oats",
            "image_url": "https://images.openfoodfacts.org/rolled.jpg",
        },
    })
    assert result["found"] is True
    assert result["name"] == "Rolled Oats"
    assert result["image_url"] == "https://images.openfoodfacts.org/rolled.jpg"


def test__is_plausible_ean__accepts_common_formats():
    assert off_lookup._is_plausible_ean("12345678")           # EAN-8
    assert off_lookup._is_plausible_ean("012345678905")       # UPC-A
    assert off_lookup._is_plausible_ean("1234567890123")      # EAN-13
    assert off_lookup._is_plausible_ean("12345678901234")     # ITF-14


def test__is_plausible_ean__rejects_dora_scheme_and_junk():
    assert not off_lookup._is_plausible_ean("dora://stock-item/abc")
    assert not off_lookup._is_plausible_ean("abc123")
    assert not off_lookup._is_plausible_ean("123")            # too short
    assert not off_lookup._is_plausible_ean("123456789012345")  # too long


def test__lookup_ean__caches_result_across_calls(monkeypatch):
    _reset_cache()
    calls = {"count": 0}

    def fake_fetch(ean: str) -> dict:
        calls["count"] += 1
        return _fake_off_hit(name=f"item-{ean}")

    monkeypatch.setattr(off_lookup, "_fetch_from_off", fake_fetch)

    first = off_lookup._lookup_ean("0123456789012")
    second = off_lookup._lookup_ean("0123456789012")

    assert calls["count"] == 1, "second lookup should hit cache, not network"
    assert first == second
    assert first["name"] == "item-0123456789012"


def test__lookup_ean__cache_expiry_refetches(monkeypatch):
    _reset_cache()
    calls = {"count": 0}

    def fake_fetch(ean: str) -> dict:
        calls["count"] += 1
        return _fake_off_hit()

    monkeypatch.setattr(off_lookup, "_fetch_from_off", fake_fetch)
    off_lookup._lookup_ean("0123456789012")
    # Rewind the cached fetch time past TTL — next call must refetch.
    fetched_at, payload = off_lookup._CACHE["0123456789012"]
    off_lookup._CACHE["0123456789012"] = (
        fetched_at - off_lookup._CACHE_TTL_SECONDS - 1, payload,
    )
    off_lookup._lookup_ean("0123456789012")
    assert calls["count"] == 2


def test__lookup_ean__cache_eviction_bounded(monkeypatch):
    _reset_cache()
    # Bound the cache tight for the test so we don't have to populate 512
    # entries.
    monkeypatch.setattr(off_lookup, "_CACHE_MAX_ENTRIES", 3)
    monkeypatch.setattr(off_lookup, "_fetch_from_off", lambda ean: _fake_off_hit())

    for ean in ["1111111111111", "2222222222222", "3333333333333", "4444444444444"]:
        off_lookup._lookup_ean(ean)

    # First-inserted key evicted, most-recent kept.
    assert "1111111111111" not in off_lookup._CACHE
    assert "4444444444444" in off_lookup._CACHE
    assert len(off_lookup._CACHE) == 3


def test__fetch_from_off__network_failure_returns_not_found(monkeypatch):
    """A URLError from `urlopen` must resolve to `{found: false}` so the
    SPA can show the manual-entry fallback without a special error branch."""
    _reset_cache()

    def raise_urlerror(*_args, **_kwargs):
        from urllib.error import URLError
        raise URLError("network down")

    monkeypatch.setattr(off_lookup, "urlopen", raise_urlerror)

    result = off_lookup._fetch_from_off("0123456789012")
    assert result == {"found": False}


def test__fetch_from_off__non_json_body_returns_not_found(monkeypatch):
    """OFF occasionally returns HTML error pages under load; JSON parse
    failures resolve to `{found: false}` for the same reason as above."""
    _reset_cache()

    class _FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *_a):
            pass
        def read(self):
            return b"<html>rate limited</html>"

    monkeypatch.setattr(off_lookup, "urlopen", lambda *_a, **_kw: _FakeResponse())
    result = off_lookup._fetch_from_off("0123456789012")
    assert result == {"found": False}
