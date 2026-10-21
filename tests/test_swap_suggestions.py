"""FU-451 — recipe-swap ranker unit tests.

Drives the pure `rank_recipe_swaps` with fixture recipes/entries — no DB, no
HTTP. The repo-touching orchestrator (`compute_suggestions`) + the apply/undo
endpoints are covered end-to-end by `tests/e2e/dora_api/test_swap_suggestions.py`.

Design lock: PROPOSAL_BUDGET_DEFENSE_SWAPS.md §4c / §5.
"""
from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from dora_api.features.meal_plans.swap_suggestions import (
    CHIP_COOKABLE, CHIP_HOUSEHOLD_FAV, CHIP_SIMILAR, rank_recipe_swaps,
)
from dora_api.features.recipes.recipe_cost import CostEstimate


def _recipe(name, *, cost, servings=2, cookable=None, cuisine_id=None,
            category_id=None, last_made_on=None, missing=None):
    rid = uuid4()
    dto = SimpleNamespace(
        recipe_id=rid, name=name, servings=servings, cookable=cookable,
        cuisine_id=cuisine_id, category_id=category_id,
        last_made_on=last_made_on, missing_stock_item_names=missing or [],
    )
    return rid, dto, CostEstimate(estimated_cost=cost, priced_count=1, total_count=1)


def _entry(recipe_id, name, *, servings=2, consumed=False):
    return SimpleNamespace(
        meal_plan_entry_id=uuid4(), recipe_id=recipe_id, recipe_name=name,
        scheduled_for=date(2026, 7, 9), slot="dinner", servings=servings,
        consumed_at=(date(2026, 7, 8) if consumed else None),
    )


def test__cheaper_cookable_candidate__wins_with_cookable_chip():
    cuisine = uuid4()
    from_id, from_dto, from_cost = _recipe("Stroganoff", cost=12.0, cuisine_id=cuisine)
    chp_id, chp_dto, chp_cost = _recipe(
        "Tray-bake", cost=6.0, cookable=True, cuisine_id=cuisine,
        missing=["Chicken", "Rosemary"],
    )
    recipes = {from_id: from_dto, chp_id: chp_dto}
    costs = {from_id: from_cost, chp_id: chp_cost}
    entry = _entry(from_id, "Stroganoff")

    out = rank_recipe_swaps([entry], recipes, costs, planned_recipe_ids={from_id})
    assert len(out) == 1
    c = out[0]
    assert c.to_recipe_id == chp_id
    assert c.reason_chip == CHIP_COOKABLE
    assert c.saved == 6.0
    assert c.missing_ingredient_names == ["Chicken", "Rosemary"]


def test__no_cheaper_candidate__no_suggestion():
    from_id, from_dto, from_cost = _recipe("Cheap dish", cost=4.0, cookable=True)
    other_id, other_dto, other_cost = _recipe("Pricey dish", cost=9.0, cookable=True)
    out = rank_recipe_swaps(
        [_entry(from_id, "Cheap dish")],
        {from_id: from_dto, other_id: other_dto},
        {from_id: from_cost, other_id: other_cost},
        planned_recipe_ids={from_id},
    )
    assert out == []


def test__consumed_entry__never_swapped():
    from_id, from_dto, from_cost = _recipe("Eaten", cost=12.0, cookable=True)
    ch_id, ch_dto, ch_cost = _recipe("Cheaper", cost=5.0, cookable=True)
    out = rank_recipe_swaps(
        [_entry(from_id, "Eaten", consumed=True)],
        {from_id: from_dto, ch_id: ch_dto},
        {from_id: from_cost, ch_id: ch_cost},
        planned_recipe_ids={from_id},
    )
    assert out == []


def test__already_planned_recipe__not_suggested():
    # The cheaper option is already on the plan this week → excluded.
    from_id, from_dto, from_cost = _recipe("Expensive", cost=12.0)
    planned_id, planned_dto, planned_cost = _recipe("Also planned", cost=5.0, cookable=True)
    out = rank_recipe_swaps(
        [_entry(from_id, "Expensive")],
        {from_id: from_dto, planned_id: planned_dto},
        {from_id: from_cost, planned_id: planned_cost},
        planned_recipe_ids={from_id, planned_id},
    )
    assert out == []


def test__stranger_recipe__filtered_out():
    # Cheaper but not cookable, no shared tag, never cooked → not pushed.
    from_id, from_dto, from_cost = _recipe("Expensive", cost=12.0, cuisine_id=uuid4())
    stranger_id, stranger_dto, stranger_cost = _recipe(
        "Random cheap thing", cost=3.0, cookable=False,
        cuisine_id=uuid4(), category_id=uuid4(), last_made_on=None,
    )
    out = rank_recipe_swaps(
        [_entry(from_id, "Expensive")],
        {from_id: from_dto, stranger_id: stranger_dto},
        {from_id: from_cost, stranger_id: stranger_cost},
        planned_recipe_ids={from_id},
    )
    assert out == []


def test__similar_and_fav_chips_assigned():
    cuisine = uuid4()
    from_id, from_dto, from_cost = _recipe("Base", cost=12.0, cuisine_id=cuisine)
    sim_id, sim_dto, sim_cost = _recipe("Same cuisine", cost=8.0, cuisine_id=cuisine)
    out = rank_recipe_swaps(
        [_entry(from_id, "Base")],
        {from_id: from_dto, sim_id: sim_dto},
        {from_id: from_cost, sim_id: sim_cost},
        planned_recipe_ids={from_id},
    )
    assert out[0].reason_chip == CHIP_SIMILAR

    fav_from_id, fav_from_dto, fav_from_cost = _recipe("Base2", cost=12.0)
    fav_id, fav_dto, fav_cost = _recipe("Old favourite", cost=7.0, last_made_on=date(2026, 1, 1))
    out2 = rank_recipe_swaps(
        [_entry(fav_from_id, "Base2")],
        {fav_from_id: fav_from_dto, fav_id: fav_dto},
        {fav_from_id: fav_from_cost, fav_id: fav_cost},
        planned_recipe_ids={fav_from_id},
    )
    assert out2[0].reason_chip == CHIP_HOUSEHOLD_FAV


def test__servings_scaling__affects_saving():
    # from-recipe serves 2 at $12 (=$6/serving); entry is for 4 people → $24.
    # candidate serves 2 at $6 (=$3/serving) → $12 for 4 → saves $12.
    from_id, from_dto, from_cost = _recipe("Big", cost=12.0, servings=2)
    ch_id, ch_dto, ch_cost = _recipe("Small", cost=6.0, servings=2, cookable=True)
    out = rank_recipe_swaps(
        [_entry(from_id, "Big", servings=4)],
        {from_id: from_dto, ch_id: ch_dto},
        {from_id: from_cost, ch_id: ch_cost},
        planned_recipe_ids={from_id},
    )
    assert out[0].saved == 12.0


def test__unpriced_from_recipe__skipped():
    from_id, from_dto, _ = _recipe("Unpriced", cost=None)
    ch_id, ch_dto, ch_cost = _recipe("Cheaper", cost=5.0, cookable=True)
    out = rank_recipe_swaps(
        [_entry(from_id, "Unpriced")],
        {from_id: from_dto, ch_id: ch_dto},
        {from_id: CostEstimate(None, 0, 1), ch_id: ch_cost},
        planned_recipe_ids={from_id},
    )
    assert out == []


def test__ranked_by_saving_and_capped_at_five():
    # Six entries each with a cheaper cookable swap of increasing saving;
    # expect 5 winners, ordered by saving desc.
    entries = []
    recipes = {}
    costs = {}
    for i in range(6):
        f_id, f_dto, f_cost = _recipe(f"from{i}", cost=20.0)
        c_id, c_dto, c_cost = _recipe(f"to{i}", cost=20.0 - (i + 1), cookable=True)
        recipes[f_id] = f_dto; recipes[c_id] = c_dto
        costs[f_id] = f_cost; costs[c_id] = c_cost
        entries.append(_entry(f_id, f"from{i}"))
    planned = {e.recipe_id for e in entries}
    out = rank_recipe_swaps(entries, recipes, costs, planned)
    assert len(out) == 5
    savings = [c.saved for c in out]
    assert savings == sorted(savings, reverse=True)
