"""FU-593 — suggestion feed fairness unit tests.

Drives the pure `_select_for_display` with fixture `Suggestion`s — no DB, no
HTTP. Pins the contract that one noisy high-severity category (e.g.
`use_soon`) can't fill the whole 8-slot cap and silently starve a
low-severity-but-distinct nudge (e.g. `reconcile_meals_pending`).
"""
from dora_api.features.suggestions.generators import (
    KIND_RECONCILE_MEALS_PENDING,
    KIND_USE_SOON,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    Suggestion,
)
from dora_api.features.suggestions.suggestions import _select_for_display


def _sugg(kind: str, severity: str, key: str) -> Suggestion:
    return Suggestion(
        kind=kind,
        dedup_key=key,
        severity=severity,
        title=f"{kind}-{key}",
        body="",
        reason="",
    )


def test__under_limit__returns_all_severity_ordered():
    items = [
        _sugg(KIND_USE_SOON, SEVERITY_LOW, "a"),
        _sugg(KIND_USE_SOON, SEVERITY_HIGH, "b"),
        _sugg(KIND_RECONCILE_MEALS_PENDING, SEVERITY_MEDIUM, "c"),
    ]
    result = _select_for_display(items, limit=8)
    assert len(result) == 3
    # Severity desc: high, medium, low.
    assert [s.severity for s in result] == [SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW]


def test__noisy_high_kind_does_not_crowd_out_a_distinct_low_nudge():
    # 10 HIGH use_soon cards would fill the whole cap under a plain
    # severity-desc truncation, dropping the lone LOW reconcile card.
    items = [_sugg(KIND_USE_SOON, SEVERITY_HIGH, str(i)) for i in range(10)]
    items.append(_sugg(KIND_RECONCILE_MEALS_PENDING, SEVERITY_LOW, "recon"))

    result = _select_for_display(items, limit=8)

    assert len(result) == 8
    kinds = {s.kind for s in result}
    # The distinct low-severity kind survives...
    assert KIND_RECONCILE_MEALS_PENDING in kinds
    # ...and the remaining 7 slots go to the noisy high-severity kind.
    assert sum(1 for s in result if s.kind == KIND_USE_SOON) == 7


def test__each_firing_kind_gets_at_least_one_slot():
    # One card of six distinct kinds + extra use_soon noise; every kind
    # should appear even though use_soon has the most (and highest) cards.
    distinct_kinds = [
        KIND_USE_SOON,
        "over_budget",
        "likely_due",
        "frequent_waster",
        "pantry_check",
        KIND_RECONCILE_MEALS_PENDING,
    ]
    items = [_sugg(k, SEVERITY_MEDIUM, "first") for k in distinct_kinds]
    items += [_sugg(KIND_USE_SOON, SEVERITY_HIGH, str(i)) for i in range(10)]

    result = _select_for_display(items, limit=8)

    assert len(result) == 8
    assert set(distinct_kinds).issubset({s.kind for s in result})


def test__final_selection_is_severity_ordered():
    items = [_sugg(KIND_USE_SOON, SEVERITY_HIGH, str(i)) for i in range(9)]
    items.append(_sugg(KIND_RECONCILE_MEALS_PENDING, SEVERITY_LOW, "recon"))

    result = _select_for_display(items, limit=8)

    ranks = ["high", "medium", "low"]
    positions = [ranks.index(s.severity) for s in result]
    assert positions == sorted(positions), "result must be severity-desc ordered"
