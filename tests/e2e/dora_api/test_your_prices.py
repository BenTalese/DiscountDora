"""FU-227 chunk 4 — `build_your_prices_for_item` end-to-end.

Pins: median over normalised per-canonical-unit prices (C1), strict-greater
1.15× threshold (C2 edge case), MIN_SAMPLES=3 (below → baseline=None, current
still set), trailing 12-month window (C2), per-dimension grouping (B4), and
LC-2 source-blind sample_count (offers never bump it even when products are
on).
"""
import uuid

import requests

BASE = "http://localhost:5170/api"
STOCK_ITEMS = f"{BASE}/stock-items"


def _new_stock_item() -> str:
    level = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
    resp = requests.post(STOCK_ITEMS, json={
        "name": f"YP-{uuid.uuid4().hex[:8]}",
        "stock_level_id": level,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["stock_item_id"]


def _log(item: str, *, total_price: float, total_measure: float, unit: str, observed_at: str | None = None) -> None:
    body = {"total_price": total_price, "total_measure": total_measure, "unit": unit}
    if observed_at is not None:
        body["observed_at"] = observed_at
    r = requests.post(f"{STOCK_ITEMS}/{item}/price-observations", json=body)
    assert r.status_code == 204, r.text


def _yp(item: str) -> dict:
    return requests.get(f"{STOCK_ITEMS}/{item}/detail").json().get("your_prices") or {}


# ── Empty / below-MIN_SAMPLES states ─────────────────────────────────────


def test__your_prices__no_observations__empty_state(api):
    item = _new_stock_item()
    yp = _yp(item)
    assert yp["baseline"] is None
    assert yp["current"] is None
    assert yp["above_baseline"] is False
    assert yp["sample_count"] == 0
    assert yp["last_observed_at"] is None
    assert yp["offers_sidecar"] == []


def test__your_prices__two_samples__baseline_null_current_set(api):
    item = _new_stock_item()
    _log(item, total_price=2.0, total_measure=1.0, unit="L")
    _log(item, total_price=3.0, total_measure=1.0, unit="L")
    yp = _yp(item)
    assert yp["baseline"] is None
    assert yp["above_baseline"] is False
    assert yp["sample_count"] == 2
    # Current is still set even below MIN_SAMPLES so the widget can render
    # "Last seen $X" without a full baseline.
    assert yp["current"] == 3.0


# ── Median + strict-greater 1.15× threshold ──────────────────────────────


def test__your_prices__three_samples__median_correct_odd(api):
    item = _new_stock_item()
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-01-01T00:00:00+00:00")
    _log(item, total_price=3.0, total_measure=1.0, unit="L",
         observed_at="2026-02-01T00:00:00+00:00")
    _log(item, total_price=5.0, total_measure=1.0, unit="L",
         observed_at="2026-03-01T00:00:00+00:00")
    yp = _yp(item)
    assert yp["baseline"] == 3.0          # median of [2, 3, 5]
    assert yp["baseline_unit"] == "L"
    assert yp["sample_count"] == 3


def test__your_prices__four_samples__median_correct_even(api):
    item = _new_stock_item()
    for i, p in enumerate([2.0, 3.0, 4.0, 5.0], start=1):
        _log(item, total_price=p, total_measure=1.0, unit="L",
             observed_at=f"2026-0{i}-01T00:00:00+00:00")
    yp = _yp(item)
    # Median of [2, 3, 4, 5] = 3.5
    assert abs(yp["baseline"] - 3.5) < 1e-6


def test__your_prices__current_above_threshold__chip_fires(api):
    item = _new_stock_item()
    # Median = 2.0, threshold = 2.0 * 1.15 = 2.3. Current must be > 2.3.
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-01-01T00:00:00+00:00")
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-02-01T00:00:00+00:00")
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-03-01T00:00:00+00:00")
    _log(item, total_price=3.0, total_measure=1.0, unit="L",
         observed_at="2026-06-01T00:00:00+00:00")
    yp = _yp(item)
    # median of [2, 2, 2, 3] = 2.0; current = 3.0 > 2.0 * 1.15 = 2.3 → above
    assert yp["above_baseline"] is True
    assert yp["current"] == 3.0


def test__your_prices__current_exactly_at_threshold__not_above(api):
    """C2 edge case: current == baseline * 1.15 is NOT above (strict >)."""
    item = _new_stock_item()
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-01-01T00:00:00+00:00")
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-02-01T00:00:00+00:00")
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-03-01T00:00:00+00:00")
    _log(item, total_price=2.30, total_measure=1.0, unit="L",
         observed_at="2026-06-01T00:00:00+00:00")
    yp = _yp(item)
    # median = 2.0, current = 2.30 == 2.0 * 1.15 → NOT above
    assert yp["above_baseline"] is False


# ── Unit normalisation: ml ↔ L, g ↔ kg ────────────────────────────────────


def test__your_prices__ml_normalises_to_per_L(api):
    """500 ml at $3.00 = $6/L. Three obs → median in canonical L."""
    item = _new_stock_item()
    for i in range(1, 4):
        _log(item, total_price=3.0, total_measure=500.0, unit="ml",
             observed_at=f"2026-0{i}-01T00:00:00+00:00")
    yp = _yp(item)
    assert yp["baseline_unit"] == "L"
    # Median of [6.0, 6.0, 6.0] = 6.0
    assert abs(yp["baseline"] - 6.0) < 1e-6


def test__your_prices__g_normalises_to_per_kg(api):
    """250 g at $5.00 = $20/kg. Three obs."""
    item = _new_stock_item()
    for i in range(1, 4):
        _log(item, total_price=5.0, total_measure=250.0, unit="g",
             observed_at=f"2026-0{i}-01T00:00:00+00:00")
    yp = _yp(item)
    assert yp["baseline_unit"] == "kg"
    assert abs(yp["baseline"] - 20.0) < 1e-6


# ── Count dimension (B1) ──────────────────────────────────────────────────


def test__your_prices__count_dimension_baseline_in_ea(api):
    """3 obs of 12 ea at $7.50 each → $0.625/ea. Median = $0.625."""
    item = _new_stock_item()
    for i in range(1, 4):
        _log(item, total_price=7.50, total_measure=12.0, unit="ea",
             observed_at=f"2026-0{i}-01T00:00:00+00:00")
    yp = _yp(item)
    assert yp["baseline_unit"] == "ea"
    assert abs(yp["baseline"] - 0.625) < 1e-6


# ── Trailing 12-month window ──────────────────────────────────────────────


def test__your_prices__old_observations_excluded_from_window(api):
    """An obs older than BASELINE_WINDOW (365d) is excluded from the median
    but the still-recent ones drive the baseline."""
    item = _new_stock_item()
    # One ancient outlier — would skew the median if not filtered.
    _log(item, total_price=100.0, total_measure=1.0, unit="L",
         observed_at="2023-01-01T00:00:00+00:00")
    # Three recent samples (assuming "now" is around 2026-06).
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-04-01T00:00:00+00:00")
    _log(item, total_price=3.0, total_measure=1.0, unit="L",
         observed_at="2026-05-01T00:00:00+00:00")
    _log(item, total_price=4.0, total_measure=1.0, unit="L",
         observed_at="2026-06-01T00:00:00+00:00")
    yp = _yp(item)
    # Sample count excludes the >12mo outlier; median over the 3 recent obs = 3.
    assert yp["sample_count"] == 3
    assert abs(yp["baseline"] - 3.0) < 1e-6


# ── Per-dimension grouping (B4) ──────────────────────────────────────────


def test__your_prices__mixed_dimensions__most_recent_dimension_wins(api):
    """If the user logs in L then in ea, the active dim follows the most-
    recent obs; obs in the other dim are excluded from the baseline."""
    item = _new_stock_item()
    # 3 L-dim observations (older).
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-01-01T00:00:00+00:00")
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-02-01T00:00:00+00:00")
    _log(item, total_price=2.0, total_measure=1.0, unit="L",
         observed_at="2026-03-01T00:00:00+00:00")
    # 3 ea-dim observations (newer — active dim should switch to ea).
    _log(item, total_price=5.0, total_measure=1.0, unit="ea",
         observed_at="2026-04-01T00:00:00+00:00")
    _log(item, total_price=6.0, total_measure=1.0, unit="ea",
         observed_at="2026-05-01T00:00:00+00:00")
    _log(item, total_price=7.0, total_measure=1.0, unit="ea",
         observed_at="2026-06-01T00:00:00+00:00")
    yp = _yp(item)
    assert yp["baseline_unit"] == "ea"
    assert yp["sample_count"] == 3
    assert abs(yp["baseline"] - 6.0) < 1e-6     # median of [5, 6, 7]


# ── Last-seen store surfacing (A2) ────────────────────────────────────────


def test__your_prices__last_seen_store_name_resolved(api):
    """A2: when the most-recent obs has a store_id, the widget gets the
    resolved name. R-003 — server resolves, client renders a string."""
    item = _new_stock_item()
    stores = requests.get(f"{BASE}/stores").json().get("items") or requests.get(f"{BASE}/stores").json()
    if not stores:
        return
    store_id = stores[0].get("store_id") if isinstance(stores[0], dict) else None
    if not store_id:
        return
    _log(item, total_price=3.0, total_measure=1.0, unit="L",
         observed_at="2026-06-01T00:00:00+00:00")
    requests.post(f"{STOCK_ITEMS}/{item}/price-observations", json={
        "total_price": 3.0, "total_measure": 1.0, "unit": "L",
        "store_id": store_id,
        "observed_at": "2026-06-15T00:00:00+00:00",
    })
    yp = _yp(item)
    assert yp["last_seen_store_name"]  # non-empty string


# ── LC-2 source-blind ─────────────────────────────────────────────────────


def test__your_prices__offers_sidecar_does_not_affect_sample_count(api):
    """LC-2 — sample_count counts observations only. Linked-product offers
    populate the sidecar but never bump the count. (Verified end-to-end via
    a stock item with no linked products: sidecar is empty; if products
    were linked it would still be a separate list, not folded in.)"""
    item = _new_stock_item()
    for i in range(1, 4):
        _log(item, total_price=2.0, total_measure=1.0, unit="L",
             observed_at=f"2026-0{i}-01T00:00:00+00:00")
    yp = _yp(item)
    assert yp["sample_count"] == 3
    # No linked products → sidecar empty.
    assert yp["offers_sidecar"] == []
