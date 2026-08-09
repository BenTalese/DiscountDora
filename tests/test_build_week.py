"""FU-596 — "Build my week" auto-planner ranker unit tests.

Drives the pure ranker (`select_recipes` / `place_entries` / `apply_budget_cap`
/ `_fill_one_day` / `_buildable_days` / `reason_chip`) with fixture candidates —
no DB, no HTTP. The repo-touching orchestrator (`compute_auto_build`) + the
endpoint are covered end-to-end by `tests/e2e/dora_api/test_meal_plan_router.py`.
"""
from datetime import date
from uuid import uuid4

from dora_api.features.meal_plans.build_week import (
    CHIP_BUDGET, CHIP_COOKABLE_NOW, CHIP_FAVOURITE, CHIP_NOT_MADE_RECENTLY,
    CHIP_USES_EXPIRING, EMPHASIS_FAVOURITES, EMPHASIS_SURPRISE,
    EMPHASIS_USE_UP_STOCK, EMPHASIS_VARIETY, RecipeCandidate, _buildable_days,
    _fill_one_day, apply_budget_cap, place_entries, reason_chip, select_recipes)


def _cand(name, *, time_of_day=None, cookable=None, expiring=0, favourite=False,
          plan_count=0, not_recent=False, cuisine=None, category=None,
          cost=None, servings=2):
    return RecipeCandidate(
        recipe_id=uuid4(), name=name, time_of_day=time_of_day, cookable=cookable,
        expiring_count=expiring, is_favourite=favourite, plan_count=plan_count,
        not_made_recently=not_recent, cuisine_id=cuisine, category_id=category,
        estimated_cost=cost, servings=servings, missing_stock_item_names=(),
    )


# ── select_recipes — emphasis weighting ────────────────────────────────────


def test__use_up_stock__prefers_expiring_then_cookable():
    expiring = _cand("zeta", expiring=2, cuisine=uuid4())
    cookable = _cand("yankee", cookable=True, cuisine=uuid4())
    plain = _cand("xray", cuisine=uuid4())
    out = select_recipes([plain, cookable, expiring], EMPHASIS_USE_UP_STOCK, 2, set())
    assert {c.name for c in out} == {"zeta", "yankee"}
    assert out[0].name == "zeta"  # expiring outranks cookable-now


def test__favourites__prefers_favourites():
    fav = _cand("fav", favourite=True, cuisine=uuid4())
    other = _cand("other", cuisine=uuid4())
    out = select_recipes([other, fav], EMPHASIS_FAVOURITES, 1, set())
    assert [c.name for c in out] == ["fav"]


def test__variety__spreads_cuisines_not_four_of_one():
    a = uuid4()
    pool = [
        _cand("a1", not_recent=True, cuisine=a),
        _cand("a2", not_recent=True, cuisine=a),
        _cand("a3", not_recent=True, cuisine=a),
        _cand("b1", not_recent=True, cuisine=uuid4()),
        _cand("c1", not_recent=True, cuisine=uuid4()),
    ]
    out = select_recipes(pool, EMPHASIS_VARIETY, 3, set())
    assert len({c.cuisine_id for c in out}) == 3  # three distinct cuisines


def test__excludes_already_planned():
    keep = _cand("keep", favourite=True, cuisine=uuid4())
    planned = _cand("planned", favourite=True, cuisine=uuid4())
    out = select_recipes([keep, planned], EMPHASIS_FAVOURITES, 5, {planned.recipe_id})
    assert [c.name for c in out] == ["keep"]  # planned excluded, distinct only


def test__count_capped_at_distinct_pool():
    pool = [_cand("one", cuisine=uuid4()), _cand("two", cuisine=uuid4())]
    out = select_recipes(pool, EMPHASIS_USE_UP_STOCK, 10, set())
    assert len(out) == 2  # never repeats a recipe to hit the count


def test__surprise__is_deterministic_for_a_seed_and_respects_exclusions():
    import random
    pool = [_cand(f"r{i}", not_recent=True, cuisine=uuid4()) for i in range(6)]
    excluded = {pool[0].recipe_id}
    out = select_recipes(pool, EMPHASIS_SURPRISE, 3, excluded, random.Random(1))
    assert len(out) == 3
    assert pool[0].recipe_id not in {c.recipe_id for c in out}


def test__reshuffle__different_rng_varies_the_pick_when_the_pool_has_slack():
    # The "Reshuffle" bug: use_up_stock was fully deterministic, so a fresh
    # request returned the identical plan. With a per-request rng the picked
    # set now varies while still honouring the emphasis.
    import random
    # Equal-signal candidates (all cookable) so only the tiebreak decides.
    pool = [_cand(f"r{i}", cookable=True, cuisine=uuid4()) for i in range(10)]
    picks = {
        frozenset(c.recipe_id for c in select_recipes(
            pool, EMPHASIS_USE_UP_STOCK, 3, set(), random.Random(seed)))
        for seed in range(8)
    }
    assert len(picks) > 1  # not always the same three


def test__reshuffle__no_rng_is_still_deterministic():
    pool = [_cand(f"r{i}", cookable=True, cuisine=uuid4()) for i in range(10)]
    a = [c.recipe_id for c in select_recipes(pool, EMPHASIS_USE_UP_STOCK, 3, set())]
    b = [c.recipe_id for c in select_recipes(pool, EMPHASIS_USE_UP_STOCK, 3, set())]
    assert a == b


def test__reshuffle__strong_signal_still_wins_over_the_tiebreak():
    # A single strongly-expiring recipe outranks the jitter every time.
    import random
    hot = _cand("hot", expiring=3, cuisine=uuid4())
    pool = [hot] + [_cand(f"r{i}", cookable=True, cuisine=uuid4()) for i in range(9)]
    for seed in range(8):
        out = select_recipes(pool, EMPHASIS_USE_UP_STOCK, 3, set(), random.Random(seed))
        assert hot.recipe_id in {c.recipe_id for c in out}


# ── _fill_one_day + place_entries — day×slot cell filling ──────────────────


def test__fill_one_day__recipe_claims_its_own_time_of_day_slot():
    # "b" names Dinner, so it wins Dinner even though "a" outranks it.
    a, b = _cand("a"), _cand("b", time_of_day="Dinner")
    out = _fill_one_day([a, b], ["Breakfast", "Dinner"])
    assert out == [(a, "Breakfast"), (b, "Dinner")]


def test__fill_one_day__falls_to_rank_order_when_no_time_of_day():
    a, b, c = _cand("a"), _cand("b"), _cand("c")
    out = _fill_one_day([a, b, c], ["Breakfast", "Lunch", "Dinner"])
    assert out == [(a, "Breakfast"), (b, "Lunch"), (c, "Dinner")]


def test__fill_one_day__time_of_day_outside_the_chosen_slots_ignored():
    c = _cand("dish", time_of_day="Snack")
    assert _fill_one_day([c], ["Dinner"]) == [(c, "Dinner")]


def test__fill_one_day__short_pool_leaves_later_slots_empty():
    a = _cand("a")
    assert _fill_one_day([a], ["Breakfast", "Lunch"]) == [(a, "Breakfast")]


def test__place_entries__one_meal_per_day_slot_cell():
    d0, d1 = date(2026, 8, 3), date(2026, 8, 4)
    picks = [_cand("a"), _cand("b"), _cand("c"), _cand("d")]
    placements = place_entries(picks, [d0, d1], ["Lunch", "Dinner"])
    assert [(day, slot) for (_c, day, slot) in placements] == [
        (d0, "Lunch"), (d0, "Dinner"), (d1, "Lunch"), (d1, "Dinner"),
    ]
    # Every cell gets a distinct recipe — no repeats across the week.
    assert len({c.recipe_id for (c, _d, _s) in placements}) == 4


def test__place_entries__does_not_dump_everything_in_first_slot():
    # The FU-596 regression: with a multi-slot pool and no time_of_day, meals
    # must spread across slots rather than all landing in the first one.
    d0 = date(2026, 8, 3)
    picks = [_cand("a"), _cand("b"), _cand("c")]
    placements = place_entries(picks, [d0], ["Breakfast", "Lunch", "Dinner"])
    assert sorted(slot for (_c, _d, slot) in placements) == ["Breakfast", "Dinner", "Lunch"]


def test__place_entries__repeat_same_day__duplicates_one_line_up():
    d0, d1, d2 = date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5)
    a, b = _cand("a"), _cand("b")
    placements = place_entries([a, b], [d0, d1, d2], ["Lunch", "Dinner"], repeat_same_day=True)
    assert len(placements) == 6
    # The same (recipe, slot) pattern on every selected day.
    for day in (d0, d1, d2):
        assert [(c.name, slot) for (c, d, slot) in placements if d == day] == [
            ("a", "Lunch"), ("b", "Dinner"),
        ]


def test__place_entries__no_days__places_nothing():
    assert place_entries([_cand("a")], [], ["Dinner"]) == []


# ── apply_budget_cap ────────────────────────────────────────────────────────


def test__budget_cap__swaps_dearest_for_cheaper():
    dear = _cand("dear", cost=10.0)
    mid = _cand("mid", cost=5.0)
    cheap = _cand("cheap", cost=2.0)
    selected, swapped = apply_budget_cap([dear, mid], [cheap], budget_remaining=8.0)
    names = {c.name for c in selected}
    assert names == {"cheap", "mid"}
    assert cheap.recipe_id in swapped


def test__budget_cap__no_cheaper_alternative__unchanged():
    dear = _cand("dear", cost=10.0)
    selected, swapped = apply_budget_cap([dear], [], budget_remaining=1.0)
    assert [c.name for c in selected] == ["dear"]
    assert swapped == set()


# ── reason_chip ─────────────────────────────────────────────────────────────


def test__reason_chip__priorities():
    assert reason_chip(_cand("x", expiring=1), EMPHASIS_USE_UP_STOCK, False) == CHIP_USES_EXPIRING
    assert reason_chip(_cand("x", cookable=True), EMPHASIS_USE_UP_STOCK, False) == CHIP_COOKABLE_NOW
    assert reason_chip(_cand("x", favourite=True), EMPHASIS_FAVOURITES, False) == CHIP_FAVOURITE
    assert reason_chip(_cand("x", not_recent=True), EMPHASIS_VARIETY, False) == CHIP_NOT_MADE_RECENTLY
    assert reason_chip(_cand("x", cost=2.0), EMPHASIS_USE_UP_STOCK, True) == CHIP_BUDGET


# ── _buildable_days ─────────────────────────────────────────────────────────


def test__buildable_days__drops_past_days_and_keeps_today():
    today = date(2026, 7, 29)  # Wednesday
    requested = [date(2026, 7, 27), date(2026, 7, 29), date(2026, 7, 31)]
    assert _buildable_days(requested, today) == [date(2026, 7, 29), date(2026, 7, 31)]


def test__buildable_days__de_duplicates_and_orders():
    today = date(2026, 7, 29)
    requested = [date(2026, 7, 31), date(2026, 7, 30), date(2026, 7, 31)]
    assert _buildable_days(requested, today) == [date(2026, 7, 30), date(2026, 7, 31)]


def test__buildable_days__all_past__empty():
    assert _buildable_days([date(2026, 7, 28)], date(2026, 7, 29)) == []
