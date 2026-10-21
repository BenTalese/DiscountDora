"""Stocktake cadence engine — unit tests for the pure resolver
(`dora_api.features.stocktake.cadence`). No DB, no HTTP.

Corresponds to PROPOSAL_STOCKTAKE_MODE §4 (Chunk 1 backend engine).
The engagement gate + endpoint wiring is covered separately by the
end-to-end pytest suite.
"""
from datetime import datetime, timedelta, timezone

from dora_api.features.stocktake.cadence import (
    CadenceBand,
    DEFAULT_BAND,
    ItemHistory,
    auto_band_from_history,
    parse_band,
    resolve_band,
)


def _now() -> datetime:
    # Fixed anchor so day-boundary arithmetic below stays stable.
    return datetime(2026, 7, 4, 12, 0, 0, tzinfo=timezone.utc)


def _ts(days_ago: int) -> datetime:
    return _now() - timedelta(days=days_ago)


# ── Bands and days ─────────────────────────────────────────────────────

def test__bands_map_to_the_expected_day_counts():
    assert CadenceBand.WEEKLY.days == 7
    assert CadenceBand.FORTNIGHTLY.days == 14
    assert CadenceBand.MONTHLY.days == 30


def test__default_band_is_fortnightly():
    assert DEFAULT_BAND is CadenceBand.FORTNIGHTLY


# ── parse_band ─────────────────────────────────────────────────────────

def test__parse_band__valid_string_round_trips():
    assert parse_band("weekly") is CadenceBand.WEEKLY
    assert parse_band("fortnightly") is CadenceBand.FORTNIGHTLY
    assert parse_band("monthly") is CadenceBand.MONTHLY


def test__parse_band__missing_or_invalid_falls_back_to_default():
    # Corrupt AppSetting should never break the queue endpoint — the
    # fallback keeps the app running with a sensible default.
    assert parse_band(None) is DEFAULT_BAND
    assert parse_band("") is DEFAULT_BAND
    assert parse_band("bogus") is DEFAULT_BAND
    assert parse_band("YEARLY") is DEFAULT_BAND


def test__parse_band__is_case_and_whitespace_tolerant():
    assert parse_band("  WEEKLY  ") is CadenceBand.WEEKLY


# ── auto_band_from_history ─────────────────────────────────────────────

def test__auto_from_history__no_signal_when_fewer_than_two_changes():
    # <2 changes in the trailing 90d window → the resolver keeps the
    # baseline instead of picking an arbitrary band from thin air.
    assert auto_band_from_history((), _now()) is None
    assert auto_band_from_history((_ts(5),), _now()) is None


def test__auto_from_history__fast_mover_reads_as_weekly():
    # Avg gap 5 days ≤ 10-day threshold.
    ts = tuple(_ts(d) for d in (0, 5, 10, 15, 20))
    assert auto_band_from_history(ts, _now()) is CadenceBand.WEEKLY


def test__auto_from_history__mid_pace_reads_as_fortnightly():
    # Avg gap 14 days — inside the 11..24 band.
    ts = tuple(_ts(d) for d in (0, 14, 28, 42))
    assert auto_band_from_history(ts, _now()) is CadenceBand.FORTNIGHTLY


def test__auto_from_history__slow_mover_reads_as_monthly():
    # Avg gap 30 days ≥ 25-day threshold.
    ts = tuple(_ts(d) for d in (0, 30, 60))
    assert auto_band_from_history(ts, _now()) is CadenceBand.MONTHLY


def test__auto_from_history__ignores_ancient_changes_beyond_the_window():
    # Two very recent changes surrounded by a huge tail from > 90 days
    # ago — only the recent pair should shape the band. The recent
    # pair is 3 days apart → Weekly.
    ts = (_ts(200), _ts(180), _ts(2), _ts(5))
    assert auto_band_from_history(ts, _now()) is CadenceBand.WEEKLY


# ── resolve_band ───────────────────────────────────────────────────────

def _plain_history() -> ItemHistory:
    return ItemHistory(
        change_timestamps=(),
        hit_low_or_out_recently=False,
        is_essential=False,
    )


def test__resolve__auto_off_uses_baseline_only():
    band = resolve_band(
        default_band=CadenceBand.MONTHLY,
        auto_enabled=False,
        history=_plain_history(),
        now=_now(),
    )
    assert band is CadenceBand.MONTHLY


def test__resolve__auto_on_but_no_history_keeps_baseline():
    # Auto only speaks when it has ≥ 2 changes — a brand-new item
    # inherits the global default rather than getting a random pick.
    band = resolve_band(
        default_band=CadenceBand.MONTHLY,
        auto_enabled=True,
        history=_plain_history(),
        now=_now(),
    )
    assert band is CadenceBand.MONTHLY


def test__resolve__auto_on_promotes_fast_mover_over_slower_baseline():
    fast = ItemHistory(
        change_timestamps=tuple(_ts(d) for d in (0, 5, 10, 15)),
        hit_low_or_out_recently=False,
        is_essential=False,
    )
    band = resolve_band(
        default_band=CadenceBand.MONTHLY,
        auto_enabled=True,
        history=fast,
        now=_now(),
    )
    assert band is CadenceBand.WEEKLY


def test__resolve__auto_can_relax_a_faster_baseline_to_monthly():
    # The self-tuner is two-way per the user's design call: a dormant
    # item drifts toward Monthly even if the household default is Weekly.
    slow = ItemHistory(
        change_timestamps=tuple(_ts(d) for d in (0, 30, 60)),
        hit_low_or_out_recently=False,
        is_essential=False,
    )
    band = resolve_band(
        default_band=CadenceBand.WEEKLY,
        auto_enabled=True,
        history=slow,
        now=_now(),
    )
    assert band is CadenceBand.MONTHLY


def test__resolve__low_or_out_recently_bumps_one_band_faster():
    hist = ItemHistory(
        change_timestamps=(),
        hit_low_or_out_recently=True,
        is_essential=False,
    )
    band = resolve_band(
        default_band=CadenceBand.FORTNIGHTLY,
        auto_enabled=False,
        history=hist,
        now=_now(),
    )
    assert band is CadenceBand.WEEKLY


def test__resolve__essential_bumps_one_band_faster():
    hist = ItemHistory(
        change_timestamps=(),
        hit_low_or_out_recently=False,
        is_essential=True,
    )
    band = resolve_band(
        default_band=CadenceBand.FORTNIGHTLY,
        auto_enabled=False,
        history=hist,
        now=_now(),
    )
    assert band is CadenceBand.WEEKLY


def test__resolve__both_bumps_stack_and_clamp_at_weekly():
    # Monthly → Fortnightly (Low/Out) → Weekly (Essential). If both
    # bumps land, we clamp at Weekly rather than trying to overshoot.
    both = ItemHistory(
        change_timestamps=(),
        hit_low_or_out_recently=True,
        is_essential=True,
    )
    band = resolve_band(
        default_band=CadenceBand.MONTHLY,
        auto_enabled=False,
        history=both,
        now=_now(),
    )
    assert band is CadenceBand.WEEKLY


def test__resolve__clamp_holds_when_starting_at_weekly():
    # Already at Weekly — no further bumps possible.
    hist = ItemHistory(
        change_timestamps=(),
        hit_low_or_out_recently=True,
        is_essential=True,
    )
    band = resolve_band(
        default_band=CadenceBand.WEEKLY,
        auto_enabled=False,
        history=hist,
        now=_now(),
    )
    assert band is CadenceBand.WEEKLY
