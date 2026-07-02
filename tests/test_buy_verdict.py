"""P8-05 — buy-verdict composer unit tests.

Every test drives `compose_verdict` with a fixture `_AxisInputs` — no
DB, no HTTP, so the composition rules can be pinned in isolation. The
data-gathering layer (`_gather_inputs`) is a thin repo walk; browser-
verify covers it end-to-end.
"""
from datetime import date, datetime, timedelta, timezone

from dora_api.features.stock_items.get_buy_verdict import (
    _AxisInputs, compose_verdict,
)


def _dt(days_ago: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days_ago)


def _today() -> date:
    return date.today()


def _rich_history_inputs(**overrides) -> _AxisInputs:
    """A middle-of-the-road history: 8 price samples over 6 months at
    around $3.80 with the most-recent shop at $3.85 (usual price band),
    buying every ~14 days, no waste events, well-stocked. Individual
    tests override the axes they care about."""
    base = _AxisInputs(
        price_samples=[
            (3.85, _dt(6)),
            (3.90, _dt(20)),
            (3.75, _dt(34)),
            (3.80, _dt(48)),
            (3.95, _dt(62)),
            (3.70, _dt(76)),
            (3.85, _dt(90)),
            (3.80, _dt(104)),
        ],
        unique_purchase_dates=sorted([
            _today() - timedelta(days=d)
            for d in (6, 20, 34, 48, 62, 76, 90, 104)
        ]),
        waste_events_12mo=0,
        purchases_12mo=8,
        stock_level_band="stocked",
        is_on_open_list=False,
        today=_today(),
    )
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


# ── Need axis trumps price ────────────────────────────────────────────

def test__out_of_stock__is_buy_with_high_confidence():
    """Charter §2.3.1: `need = out_of_stock` overrides everything —
    even if price is above usual and the user has wasted this before,
    the shelf is empty and the item needs replacing."""
    verdict = compose_verdict(_rich_history_inputs(stock_level_band="out"))
    assert verdict.verdict == "buy"
    assert verdict.confidence == "high"
    assert any(r.axis == "need" and r.signal == "out_of_stock" for r in verdict.reasons)
    assert verdict.one_tap_action.kind == "add_to_list"


def test__out_of_stock_and_above_usual_price__still_buy():
    """The price axis still contributes a reason, but the verdict
    doesn't flip. Users need to see the price warning without the
    verdict lying about the underlying need."""
    inputs = _rich_history_inputs(
        stock_level_band="out",
        # Make the last shop the priciest so `above_usual` fires.
        price_samples=[
            (4.50, _dt(6)),
            (3.80, _dt(20)),
            (3.75, _dt(34)),
            (3.80, _dt(48)),
            (3.85, _dt(62)),
        ],
    )
    verdict = compose_verdict(inputs)
    assert verdict.verdict == "buy"
    assert any(r.axis == "price" and r.signal == "above_usual" for r in verdict.reasons)


# ── Low stock branches ────────────────────────────────────────────────

def test__low_stock_plus_cheapest_3mo__is_buy_high():
    inputs = _rich_history_inputs(
        stock_level_band="low",
        # Steep drop on the most recent shop.
        price_samples=[
            (3.10, _dt(6)),
            (3.90, _dt(20)),
            (3.85, _dt(34)),
            (3.80, _dt(48)),
            (3.90, _dt(62)),
            (3.85, _dt(76)),
            (3.90, _dt(90)),
        ],
    )
    verdict = compose_verdict(inputs)
    assert verdict.verdict == "buy"
    assert verdict.confidence == "high"
    assert any(r.signal == "cheapest_3mo" for r in verdict.reasons)


def test__low_stock_plus_above_usual__is_wait():
    inputs = _rich_history_inputs(
        stock_level_band="low",
        price_samples=[
            (4.60, _dt(6)),         # ~120% of usual ($3.85)
            (3.80, _dt(20)),
            (3.85, _dt(34)),
            (3.80, _dt(48)),
            (3.85, _dt(62)),
        ],
    )
    verdict = compose_verdict(inputs)
    assert verdict.verdict == "wait"
    assert verdict.one_tap_action.kind == "skip"


def test__low_stock_plus_usual_price__is_buy_medium():
    verdict = compose_verdict(_rich_history_inputs(stock_level_band="low"))
    assert verdict.verdict == "buy"
    assert verdict.confidence == "medium"


# ── Well-stocked branches (waste + price interplay) ───────────────────

def test__well_stocked_plus_frequent_waste__is_skip_high():
    """Charter §2.3.3: 'wastes often' should trump a cheap price — you
    do not want to buy more of what you throw away."""
    inputs = _rich_history_inputs(
        stock_level_band="stocked",
        waste_events_12mo=4,
        purchases_12mo=8,          # 50% waste rate → wastes_often
        # And it happens to be the cheapest in 3 months too.
        price_samples=[
            (3.00, _dt(6)),
            (3.85, _dt(20)),
            (3.90, _dt(34)),
            (3.80, _dt(48)),
        ],
    )
    verdict = compose_verdict(inputs)
    assert verdict.verdict == "skip"
    assert verdict.confidence == "high"
    assert any(r.signal == "wastes_often" for r in verdict.reasons)
    assert verdict.one_tap_action.kind == "mark_stocked"


def test__well_stocked_plus_waste_and_on_open_list__action_is_remove():
    """If we're saying skip *and* the item is already on an open list,
    the sensible one-tap is 'remove from list', not 'mark stocked'."""
    inputs = _rich_history_inputs(
        stock_level_band="stocked",
        waste_events_12mo=4,
        purchases_12mo=8,
        is_on_open_list=True,
    )
    verdict = compose_verdict(inputs)
    assert verdict.verdict == "skip"
    assert verdict.one_tap_action.kind == "remove_from_list"


def test__well_stocked_plus_cheapest__is_buy_medium():
    inputs = _rich_history_inputs(
        stock_level_band="stocked",
        price_samples=[
            (3.10, _dt(6)),
            (3.90, _dt(20)),
            (3.85, _dt(34)),
            (3.80, _dt(48)),
            (3.85, _dt(62)),
        ],
    )
    verdict = compose_verdict(inputs)
    assert verdict.verdict == "buy"
    assert verdict.confidence == "medium"


def test__well_stocked_plus_above_usual__is_wait():
    inputs = _rich_history_inputs(
        stock_level_band="stocked",
        price_samples=[
            (4.60, _dt(6)),
            (3.85, _dt(20)),
            (3.80, _dt(34)),
            (3.90, _dt(48)),
        ],
    )
    verdict = compose_verdict(inputs)
    assert verdict.verdict == "wait"


def test__well_stocked_plus_usual_price__is_unsure_low():
    verdict = compose_verdict(_rich_history_inputs(stock_level_band="stocked"))
    assert verdict.verdict == "unsure"
    assert verdict.confidence == "low"
    assert verdict.one_tap_action.kind == "none"


# ── Thin data collapses honestly ──────────────────────────────────────

def test__all_axes_thin__collapses_to_single_not_enough_history():
    """Charter §2.3.4: three thin axes ⇒ one honest reason, not three
    absent-signal messages."""
    inputs = _AxisInputs(
        price_samples=[(3.80, _dt(4))],   # 1 sample → thin
        unique_purchase_dates=[_today() - timedelta(days=4)],
        waste_events_12mo=0,
        purchases_12mo=1,
        stock_level_band="unknown",
        is_on_open_list=False,
        today=_today(),
    )
    verdict = compose_verdict(inputs)
    assert verdict.verdict == "unsure"
    assert verdict.confidence == "low"
    assert len(verdict.reasons) == 1
    assert verdict.reasons[0].signal == "thin_data"
    assert verdict.one_tap_action.kind == "none"


def test__thin_price_only__drops_confidence_a_step_but_keeps_verdict():
    """Low-stock with thin price data: verdict stays `buy` (need trumps),
    but confidence steps down from medium to low."""
    inputs = _AxisInputs(
        price_samples=[(3.80, _dt(6))],        # 1 sample → thin
        unique_purchase_dates=[_today() - timedelta(days=6)],
        waste_events_12mo=0,
        purchases_12mo=1,
        stock_level_band="low",
        is_on_open_list=False,
        today=_today(),
    )
    verdict = compose_verdict(inputs)
    assert verdict.verdict == "buy"
    assert verdict.confidence == "low"     # stepped down from medium


def test__waste_thin_but_no_events__signals_no_waste_history_not_thin():
    """Purchase history is too shallow to compute a waste rate, but
    zero events + a fresh account is not the same as 'unknown'. The
    axis contributes no reason but confidence doesn't drop from it."""
    inputs = _AxisInputs(
        price_samples=[
            (3.80, _dt(6)),
            (3.85, _dt(20)),
            (3.75, _dt(34)),
            (3.80, _dt(48)),
        ],
        unique_purchase_dates=sorted([
            _today() - timedelta(days=d) for d in (6, 20, 34, 48)
        ]),
        waste_events_12mo=0,
        purchases_12mo=2,   # under the min-for-waste-rate threshold
        stock_level_band="stocked",
        is_on_open_list=False,
        today=_today(),
    )
    verdict = compose_verdict(inputs)
    # Well-stocked + usual price + no-waste-history → unsure/low
    # (no positive reason for a buy either). But not the 3-axis
    # collapse; there are still price + need reasons.
    assert verdict.verdict == "unsure"
    assert verdict.confidence == "low"


# ── Data-used transparency ────────────────────────────────────────────

def test__data_used_reflects_the_actual_inputs():
    """The `data_used` block is the SPA's 'why?' tooltip source — must
    match what the composer saw or the UI lies (Charter P7 preview /
    explain)."""
    inputs = _rich_history_inputs()
    verdict = compose_verdict(inputs)
    data = verdict.data_used
    assert data.price_samples == 8
    assert data.stock_level_band == "stocked"
    assert data.purchases_last_12mo == 8
    assert data.waste_events_last_12mo == 0
    assert data.average_days_between_purchase is not None
    assert data.days_since_last_purchase is not None
