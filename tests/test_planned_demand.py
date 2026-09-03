"""Planned demand + the shared cooked-batch pool model (owner, 2026-09-03).

Two pure rules are pinned here — the allocation (`allocate_pool`) and the
grading (`urgency_for`, `build_reason`) — with no DB and no HTTP, the same way
`test_pantry_belief.py` pins the belief model. The repo walk on top of them is
a thin gather; the e2e suite covers it end to end.

The thing worth pinning hardest is that **coverage is all-or-nothing per
entry**: a 4-serving meal against a 3-serving pool still has to be cooked, so
its ingredients are still demand. Getting that wrong in the generous direction
would make the signal go quiet exactly when a batch has *nearly* run out,
which is the moment it is most worth saying something.
"""
from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest

from dora_api.domain.stock_status import (LOW_STOCK_SEQUENCE,
                                          OUT_OF_STOCK_SEQUENCE,
                                          STOCKED_SEQUENCE)
from dora_api.features.meal_plans.planned_meals import (PlannedMeal,
                                                        PlannedMealSnapshot,
                                                        allocate_pool,
                                                        recipe_shortfalls)
from dora_api.features.stock_items.planned_demand import (URGENCY_BLOCKING,
                                                          URGENCY_NONE,
                                                          URGENCY_WATCH,
                                                          build_reason,
                                                          urgency_for)

_TODAY = date(2026, 9, 3)
_RECIPE = UUID("11111111-1111-1111-1111-111111111111")


def _meal(day_offset: int, servings: int = 2, recipe_id: UUID = _RECIPE,
          name: str = "Fried Rice") -> PlannedMeal:
    return PlannedMeal(
        entry_id=uuid4(),
        recipe_id=recipe_id,
        recipe_name=name,
        scheduled_for=_TODAY + timedelta(days=day_offset),
        servings=servings,
        covered=False,
    )


# ── allocate_pool ────────────────────────────────────────────────────────

def test__allocate_pool__no_pool__covers_nothing():
    meals = allocate_pool([_meal(1), _meal(3), _meal(5)], 0)
    assert [m.covered for m in meals] == [False, False, False]


def test__allocate_pool__spends_on_the_soonest_meals_first():
    # The owner's example: three planned fried rice, a pool of four servings,
    # two-serving meals — so the first two are covered and the third is not.
    meals = allocate_pool([_meal(5), _meal(1), _meal(3)], 4)
    assert [(m.scheduled_for.day, m.covered) for m in meals] == [
        (_TODAY.day + 1, True), (_TODAY.day + 3, True), (_TODAY.day + 5, False),
    ]


def test__allocate_pool__partial_coverage_does_not_count_as_covered():
    # 3 servings in the pool, a 4-serving meal: you are still cooking it.
    meals = allocate_pool([_meal(1, servings=4)], 3)
    assert meals[0].covered is False


def test__allocate_pool__leftovers_reach_a_later_smaller_meal():
    # 3 in the pool; the 4-serving meal on day 1 can't be covered, but the
    # 2-serving one on day 4 can — the pool isn't consumed by the miss.
    meals = allocate_pool([_meal(1, servings=4), _meal(4, servings=2)], 3)
    assert [m.covered for m in meals] == [False, True]


def test__allocate_pool__negative_pool_is_treated_as_empty():
    assert allocate_pool([_meal(1)], -5)[0].covered is False


# ── recipe_shortfalls ────────────────────────────────────────────────────

def test__recipe_shortfalls__pool_covers_everything__recipe_absent():
    snapshot = PlannedMealSnapshot(
        meals=allocate_pool([_meal(1), _meal(3)], 4),
        available_by_recipe={_RECIPE: 4},
    )
    assert recipe_shortfalls(snapshot) == []


def test__recipe_shortfalls__reports_the_servings_gap_and_first_uncovered_date():
    snapshot = PlannedMealSnapshot(
        meals=allocate_pool([_meal(1), _meal(3), _meal(5)], 2),
        available_by_recipe={_RECIPE: 2},
    )
    [row] = recipe_shortfalls(snapshot)
    assert row.committed_meals == 6
    assert row.available_meals == 2
    assert row.shortfall == 4
    # Day 1 is covered by the pool, so the first date anything is actually
    # needed by is day 3 — not day 1, which the old SQL would have reported.
    assert row.earliest_needed == _TODAY + timedelta(days=3)


# ── urgency_for ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("recorded,expected", [
    (OUT_OF_STOCK_SEQUENCE, URGENCY_BLOCKING),
    (LOW_STOCK_SEQUENCE, URGENCY_WATCH),
    (STOCKED_SEQUENCE, URGENCY_NONE),
    (None, URGENCY_NONE),
])
def test__urgency_for__grades_against_the_recorded_level(recorded, expected):
    assert urgency_for(recorded, needed_meals=2) == expected


def test__urgency_for__nothing_left_to_cook__is_never_urgent():
    # Every planned meal already covered by a batch: the plan wants nothing.
    assert urgency_for(OUT_OF_STOCK_SEQUENCE, needed_meals=0) == URGENCY_NONE


# ── build_reason ─────────────────────────────────────────────────────────

def test__build_reason__names_the_meals_and_the_first_date():
    reason = build_reason(
        planned_meals=3, covered_meals=0,
        recipe_names=["Fried Rice"], earliest_needed=date(2026, 9, 5),
    )
    assert reason.startswith("3 planned meals coming up need this — Fried Rice")
    assert "First needed Sat 5 Sep" in reason


def test__build_reason__mentions_the_batch_allocation_when_there_is_one():
    reason = build_reason(
        planned_meals=3, covered_meals=2,
        recipe_names=["Fried Rice"], earliest_needed=date(2026, 9, 12),
    )
    assert "2 already covered by a cooked batch" in reason


def test__build_reason__caps_the_named_recipes():
    reason = build_reason(
        planned_meals=4, covered_meals=0,
        recipe_names=["Fried Rice", "Congee", "Risotto", "Paella"],
        earliest_needed=date(2026, 9, 4),
    )
    assert "Fried Rice, Congee and 2 others" in reason
    assert "Risotto" not in reason


def test__build_reason__two_recipes__joins_with_and_not_a_comma():
    reason = build_reason(
        planned_meals=3, covered_meals=0,
        recipe_names=["Sunday Ragu", "Egg Fried Rice"],
        earliest_needed=date(2026, 9, 4),
    )
    assert "Sunday Ragu and Egg Fried Rice" in reason


def test__build_reason__no_planned_meals__says_nothing():
    assert build_reason(
        planned_meals=0, covered_meals=0, recipe_names=[], earliest_needed=None,
    ) == ""
