"""FU-317 Chunk 2 — pure-function pool helpers.

`preview_pool_after` is the projection function used by preview surfaces
(the assistant's confirm-action step). It must apply the exact same
floor rule as `bump_pool`'s SQL CASE WHEN — anything else drifts the
preview label from what the write actually does.

`bump_pool` itself is DB-bound (raw `UPDATE ... RETURNING`); its
behaviour is covered end-to-end by `tests/e2e/dora_api/test_reconcile_receipts.py`
and the cook + adjust router tests. This file pins the pure helper only.
"""
from dora_api.features.recipes.pool import preview_pool_after


def test__delta_zero__returns_current():
    assert preview_pool_after(5, 0) == 5


def test__positive_delta__adds_to_current():
    assert preview_pool_after(5, 3) == 8


def test__negative_delta_within_bounds__subtracts():
    assert preview_pool_after(5, -2) == 3


def test__negative_delta_below_zero__floors_at_zero():
    assert preview_pool_after(2, -5) == 0


def test__delta_makes_zero__returns_zero():
    assert preview_pool_after(3, -3) == 0


def test__none_current_treated_as_zero():
    # `Recipe.available_meals` is a plain int column, but legacy /
    # pre-migration rows may briefly be None in flight — mirror the
    # `or 0` guard the callers used to do inline.
    assert preview_pool_after(None, 4) == 4
    assert preview_pool_after(None, -4) == 0


def test__large_positive_delta__no_upper_bound():
    # The API layer caps requests at ±999; the pool helper itself
    # applies only the floor rule.
    assert preview_pool_after(0, 999) == 999
    assert preview_pool_after(500, 999) == 1499
