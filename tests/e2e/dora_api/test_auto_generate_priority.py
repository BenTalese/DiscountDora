"""Unit-level coverage of X5's provenance-priority merge logic.

The full HTTP path is exercised in test_shopping_lists_router.py (TBD). This
file focuses on the dedupe behaviour that the spec is most picky about —
when an item is collected by multiple sources, the line should land with
the *highest-priority* added_via tag.
"""
from uuid import uuid4

import pytest

from dora_api.domain.entities.shopping_list import (
    ADDED_VIA_AUTO_ESSENTIAL,
    ADDED_VIA_AUTO_FLAGGED,
    ADDED_VIA_AUTO_FREQUENTLY_ADDED,
    ADDED_VIA_AUTO_LOW_STOCK,
    ADDED_VIA_AUTO_MEAL_PLAN,
    ADDED_VIA_AUTO_RECIPE,
)
from dora_api.features.shopping_lists.auto_generate import (
    AutoGenerateHandler,
    _Candidate,
)


def _candidate(via):
    # The stock_item field is only used for downstream sequencing — the
    # priority merge logic ignores it.
    return _Candidate(stock_item=None, added_via=via)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "first, second, expected",
    [
        # recipe beats every other source
        (ADDED_VIA_AUTO_LOW_STOCK, ADDED_VIA_AUTO_RECIPE, ADDED_VIA_AUTO_RECIPE),
        (ADDED_VIA_AUTO_RECIPE, ADDED_VIA_AUTO_LOW_STOCK, ADDED_VIA_AUTO_RECIPE),
        (ADDED_VIA_AUTO_FLAGGED, ADDED_VIA_AUTO_RECIPE, ADDED_VIA_AUTO_RECIPE),
        # meal_plan beats flagged / essential / low / freq
        (ADDED_VIA_AUTO_FLAGGED, ADDED_VIA_AUTO_MEAL_PLAN, ADDED_VIA_AUTO_MEAL_PLAN),
        (ADDED_VIA_AUTO_ESSENTIAL, ADDED_VIA_AUTO_MEAL_PLAN, ADDED_VIA_AUTO_MEAL_PLAN),
        # flagged beats essential
        (ADDED_VIA_AUTO_ESSENTIAL, ADDED_VIA_AUTO_FLAGGED, ADDED_VIA_AUTO_FLAGGED),
        # essential beats low_stock
        (ADDED_VIA_AUTO_LOW_STOCK, ADDED_VIA_AUTO_ESSENTIAL, ADDED_VIA_AUTO_ESSENTIAL),
        # low_stock beats frequently_added
        (
            ADDED_VIA_AUTO_FREQUENTLY_ADDED,
            ADDED_VIA_AUTO_LOW_STOCK,
            ADDED_VIA_AUTO_LOW_STOCK,
        ),
        # idempotent — same source twice doesn't flip
        (ADDED_VIA_AUTO_FLAGGED, ADDED_VIA_AUTO_FLAGGED, ADDED_VIA_AUTO_FLAGGED),
    ],
)
def test_provenance_priority_picks_highest(first, second, expected):
    candidates = {}
    stock_item_id = uuid4()
    AutoGenerateHandler._merge(candidates, stock_item_id, _candidate(first))
    AutoGenerateHandler._merge(candidates, stock_item_id, _candidate(second))
    assert candidates[stock_item_id].added_via == expected


def test_provenance_priority_is_order_independent():
    # Merging in either order should reach the same final pick — the merge
    # logic is associative.
    a = _candidate(ADDED_VIA_AUTO_RECIPE)
    b = _candidate(ADDED_VIA_AUTO_MEAL_PLAN)
    c = _candidate(ADDED_VIA_AUTO_FLAGGED)

    fwd: dict = {}
    AutoGenerateHandler._merge(fwd, "x", a)
    AutoGenerateHandler._merge(fwd, "x", b)
    AutoGenerateHandler._merge(fwd, "x", c)

    rev: dict = {}
    AutoGenerateHandler._merge(rev, "x", c)
    AutoGenerateHandler._merge(rev, "x", b)
    AutoGenerateHandler._merge(rev, "x", a)

    assert fwd["x"].added_via == ADDED_VIA_AUTO_RECIPE
    assert rev["x"].added_via == ADDED_VIA_AUTO_RECIPE
