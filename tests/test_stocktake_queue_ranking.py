"""Unit tests for the stocktake queue's ordering rule
(`features/stocktake/queue_ranking.py`).

Chunk 5 / **D-1**: cadence decides who is in the queue, belief decides the
order. The rule is pure, so it's pinned here rather than inferred from the
endpoint's e2e coverage — the endpoint can only show you the first page, and
the properties that matter (a confident item sinks *below* a no-evidence one;
the no-evidence ordering is byte-for-byte the old one) are about the whole
list.
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from dora_api.features.stock_items.pantry_belief import PantryBelief
from dora_api.features.stocktake.queue_ranking import (RANK_CONFIDENT,
                                                       RANK_OVERDUE,
                                                       RANK_UNCERTAIN,
                                                       rank_for, rank_queue)

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)


@dataclass
class _Item:
    """Duck-typed StockItem — the rule reads exactly these three attributes."""
    name: str = "thing"
    last_checked_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)


def _belief(
    *,
    confidence: float,
    confidence_band: str,
    is_inferred: bool = True,
    band: str = "low",
) -> PantryBelief:
    return PantryBelief(
        believed_sequence=1,
        believed_band=band,
        confidence=confidence,
        confidence_band=confidence_band,
        reason="bought 12 days ago, you usually finish in about 14 days",
        is_inferred=is_inferred,
        differs_from_recorded=True,
    )


HIGH = _belief(confidence=0.8, confidence_band="high")
MEDIUM = _belief(confidence=0.5, confidence_band="medium")
LOW_CONF = _belief(confidence=0.2, confidence_band="low")


# ── rank_for ────────────────────────────────────────────────────────────

def test__rank_for__NoBelief__IsOverdueRank():
    """No evidence either way — cadence is the honest answer, which is what
    it always was."""
    assert rank_for(None) == RANK_OVERDUE


def test__rank_for__EchoOfAConfirmedLevel__IsOverdueRank():
    """`is_inferred=False` means the belief is echoing a level the user
    confirmed recently. That says the *record* is fresh, not that the shelf
    was counted, so it must not rank the item as known."""
    echo = _belief(confidence=0.9, confidence_band="high", is_inferred=False)
    assert rank_for(echo) == RANK_OVERDUE


def test__rank_for__ConfidentInference__IsConfidentRank():
    assert rank_for(HIGH) == RANK_CONFIDENT


def test__rank_for__MediumInference__IsUncertainRank():
    """Medium is treated as uncertain deliberately, even though the "Dora
    thinks" overlay is happy to remark on it: remarking is cheap, but ranking
    an item *down* the walk on a medium hunch risks never reaching it."""
    assert rank_for(MEDIUM) == RANK_UNCERTAIN


def test__rank_for__LowConfidenceInference__IsUncertainRank():
    assert rank_for(LOW_CONF) == RANK_UNCERTAIN


# ── rank_queue ──────────────────────────────────────────────────────────

def test__rank_queue__NoBeliefsAtAll__IsMostOverdueFirst():
    """The inference-off path, and it has to be exactly the old behaviour:
    most-overdue first. A user who opted out of inference must not have their
    queue quietly reordered by it."""
    a, b, c = _Item(name="a"), _Item(name="b"), _Item(name="c")
    ordered = rank_queue([(3, a), (30, b), (12, c)], {})

    assert [item.name for item, _ in ordered] == ["b", "c", "a"]
    assert {verdict.rank for _, verdict in ordered} == {RANK_OVERDUE}


def test__rank_queue__UncertainBeliefs__LeastCertainFirst():
    """The core of D-1: a stocktake produces information, so the best first
    item is the one we know least about — not the one the calendar has been
    nagging about longest."""
    sure_ish = _Item(name="sure-ish")
    unsure = _Item(name="unsure")
    ordered = rank_queue(
        # `sure_ish` is far more overdue, and still sorts second.
        [(40, sure_ish), (2, unsure)],
        {sure_ish.id: MEDIUM, unsure.id: LOW_CONF},
    )

    assert [item.name for item, _ in ordered] == ["unsure", "sure-ish"]


def test__rank_queue__ConfidentItem__SinksBelowNoEvidenceItems():
    """Three-rank order, and the interesting half is that `confident` sinks
    below `overdue`: Dora already worked those out from logged evidence, so
    walking to them is the least valuable trip in the list. They stay *in* the
    queue — belief has no quantity awareness and is a bad authority — they just
    go last. Chunk 6's Review phase is what finally offers them at a desk."""
    confident = _Item(name="confident")
    no_evidence = _Item(name="no-evidence")
    uncertain = _Item(name="uncertain")
    ordered = rank_queue(
        # Overdue days deliberately inverted against the expected order, so a
        # regression to "most-overdue first" fails loudly.
        [(1, uncertain), (50, confident), (25, no_evidence)],
        {confident.id: HIGH, uncertain.id: LOW_CONF},
    )

    assert [item.name for item, _ in ordered] == [
        "uncertain", "no-evidence", "confident",
    ]
    assert [verdict.rank for _, verdict in ordered] == [
        RANK_UNCERTAIN, RANK_OVERDUE, RANK_CONFIDENT,
    ]


def test__rank_queue__WithinTheSameRank__OverdueThenBaselineThenName():
    """Ties resolve deterministically. Without this the list can reshuffle
    between two calls that saw identical data, which reads as a bug and makes
    "where was I?" impossible during a walk."""
    older = _Item(name="zz-older", last_checked_at=NOW - timedelta(days=60))
    newer = _Item(name="aa-newer", last_checked_at=NOW - timedelta(days=1))
    same_a = _Item(name="aaa", last_checked_at=NOW - timedelta(days=5))
    same_b = _Item(name="bbb", last_checked_at=NOW - timedelta(days=5))

    ordered = rank_queue(
        [(5, newer), (5, same_b), (9, older), (5, same_a)], {},
    )

    # 9 days overdue leads; then the three 5-day rows by oldest baseline,
    # with the two equal baselines broken by name.
    assert [item.name for item, _ in ordered] == [
        "zz-older", "aaa", "bbb", "aa-newer",
    ]


def test__rank_queue__ItemNeverChecked__SortsAsOldest():
    """A `None` baseline is an item nobody has ever touched, which is the
    oldest thing in the pantry, not the newest. (`datetime.min`, not a 9999
    sentinel — the endpoint's own convention.)"""
    never = _Item(name="never", last_checked_at=None)
    recent = _Item(name="recent", last_checked_at=NOW - timedelta(days=2))

    ordered = rank_queue([(5, recent), (5, never)], {})

    assert [item.name for item, _ in ordered] == ["never", "recent"]


def test__rank_queue__CarriesTheBeliefThrough__SoCallersDontRecompute():
    """The DTO needs the belief's own words for the runner's caption. Handing
    it back with the verdict keeps `compute_belief` called exactly once per
    item per request (R-003)."""
    item = _Item(name="thing")
    ordered = rank_queue([(4, item)], {item.id: MEDIUM})

    _, verdict = ordered[0]
    assert verdict.belief is MEDIUM
    assert verdict.is_confident is False


def test__rank_queue__EmptyInput__IsEmpty():
    assert rank_queue([], {}) == []
