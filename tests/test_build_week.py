"""FU-596 — "Build my week" auto-planner ranker unit tests.

Drives the pure ranker (`select_recipes` / `place_entries` / `apply_budget_cap`
/ `_pick_slot` / `_scope_days` / `reason_chip`) with fixture candidates — no DB,
no HTTP. The repo-touching orchestrator (`compute_auto_build`) + the endpoint
are covered end-to-end by `tests/e2e/dora_api/test_meal_plan_router.py`.
"""
from datetime import date
from uuid import uuid4

from dora_api.features.meal_plans.build_week import (
    CHIP_BUDGET, CHIP_COOKABLE_NOW, CHIP_FAVOURITE, CHIP_NOT_MADE_RECENTLY,
    CHIP_USES_EXPIRING, EMPHASIS_FAVOURITES, EMPHASIS_SURPRISE,
    EMPHASIS_USE_UP_STOCK, EMPHASIS_VARIETY, RecipeCandidate, _pick_slot,
    _scope_days, apply_budget_cap, place_entries, reason_chip, select_recipes)


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


# ── place_entries + _pick_slot — FU-596 smart slot placement ───────────────


def test__pick_slot__honours_recipe_time_of_day():
    c = _cand("dish", time_of_day="Lunch")
    slots = ["Breakfast", "Lunch", "Dinner"]
    seq = {"Breakfast": 0, "Lunch": 1, "Dinner": 2}
    assert _pick_slot(c, slots, {"Breakfast": 0, "Lunch": 0, "Dinner": 0}, seq) == "Lunch"


def test__pick_slot__falls_to_least_loaded_when_no_time_of_day():
    c = _cand("dish")  # no time_of_day
    slots = ["Breakfast", "Lunch", "Dinner"]
    seq = {"Breakfast": 0, "Lunch": 1, "Dinner": 2}
    load = {"Breakfast": 1, "Lunch": 0, "Dinner": 1}
    assert _pick_slot(c, slots, load, seq) == "Lunch"


def test__pick_slot__time_of_day_outside_pool_ignored():
    c = _cand("dish", time_of_day="Snack")
    assert _pick_slot(c, ["Dinner"], {"Dinner": 0}, {"Dinner": 0}) == "Dinner"


def test__place_entries__spreads_day_major():
    d0, d1 = date(2026, 8, 3), date(2026, 8, 4)
    picks = [_cand("a"), _cand("b"), _cand("c")]
    placements = place_entries(picks, [d0, d1], ["Dinner"], {"Dinner": 0})
    assert [day for (_c, day, _s) in placements] == [d0, d1, d0]
    assert all(slot == "Dinner" for (_c, _d, slot) in placements)


def test__place_entries__does_not_dump_everything_in_first_slot():
    # The FU-596 regression: with a multi-slot pool and no time_of_day, meals
    # must spread across slots rather than all landing in the first one.
    d0 = date(2026, 8, 3)
    picks = [_cand("a"), _cand("b"), _cand("c")]
    slots = ["Breakfast", "Lunch", "Dinner"]
    seq = {"Breakfast": 0, "Lunch": 1, "Dinner": 2}
    placements = place_entries(picks, [d0], slots, seq)
    assert sorted(slot for (_c, _d, slot) in placements) == ["Breakfast", "Dinner", "Lunch"]


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


# ── _scope_days ─────────────────────────────────────────────────────────────


def test__scope_days__week_drops_past_days():
    monday = date(2026, 7, 27)
    today = date(2026, 7, 29)  # Wednesday
    assert _scope_days("week", monday, today) == [
        date(2026, 7, 29), date(2026, 7, 30), date(2026, 7, 31),
        date(2026, 8, 1), date(2026, 8, 2),
    ]


def test__scope_days__single_day():
    today = date(2026, 7, 29)
    assert _scope_days("day", date(2026, 7, 30), today) == [date(2026, 7, 30)]
    assert _scope_days("day", date(2026, 7, 28), today) == []  # past → empty
