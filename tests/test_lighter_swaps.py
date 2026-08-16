"""FU-637 — lighter-alternative ranker unit tests.

Drives the pure `rank_lighter_swaps` with fixture recipes — no DB, no HTTP.
Sibling of `tests/test_swap_suggestions.py` (the budget axis); the two share
the household-affinity rule, so what's pinned here is the *nutrition* half:
which figures may be compared at all, and what order the answers come back in.
"""
from types import SimpleNamespace
from uuid import uuid4

from dora_api.features.meal_plans.swap_suggestions import (
    CHIP_LIGHTER_COOKABLE,
    CHIP_LIGHTER_HOUSEHOLD_FAV,
    CHIP_LIGHTER_SIMILAR,
    MAX_LIGHTER_CANDIDATES,
    rank_lighter_swaps,
)


def _recipe(name, *, kcal, reliable=True, cookable=None, cuisine_id=None,
            category_id=None, last_made_on=None, missing=None):
    rid = uuid4()
    return rid, SimpleNamespace(
        recipe_id=rid, name=name, kcal_per_serving=kcal, kcal_is_reliable=reliable,
        cookable=cookable, cuisine_id=cuisine_id, category_id=category_id,
        last_made_on=last_made_on, missing_stock_item_names=missing or [],
    )


def _rank(from_dto, candidates, planned=None):
    recipes = {from_dto.recipe_id: from_dto}
    recipes.update({rid: dto for rid, dto in candidates})
    return rank_lighter_swaps(from_dto, recipes, planned or set())


def test__lighter_candidate__IsOfferedWithTheReductionAndChip():
    cuisine = uuid4()
    _, heavy = _recipe("Carbonara", kcal=900, cuisine_id=cuisine)
    light = _recipe("Tray-bake", kcal=550, cookable=True, cuisine_id=cuisine,
                    missing=["Chicken"])

    out = _rank(heavy, [light])

    assert len(out) == 1
    assert out[0].to_recipe_name == "Tray-bake"
    assert out[0].saved_kcal == 350
    assert out[0].kcal_per_serving == 550
    assert out[0].reason_chip == CHIP_LIGHTER_COOKABLE
    assert out[0].missing_ingredient_names == ["Chicken"]


def test__heavierOrEqualCandidates__AreNotOffered():
    cuisine = uuid4()
    _, heavy = _recipe("Carbonara", kcal=900, cuisine_id=cuisine)
    same = _recipe("Twin", kcal=900, cuisine_id=cuisine)
    heavier = _recipe("Lasagne", kcal=1100, cuisine_id=cuisine)

    assert _rank(heavy, [same, heavier]) == []


def test__unreliableCandidate__IsNeverComparedAgainst():
    # Ranking a meal against a one-of-eight estimate answers "which is
    # lighter?" with arithmetic on missing data.
    cuisine = uuid4()
    _, heavy = _recipe("Carbonara", kcal=900, cuisine_id=cuisine)
    thin = _recipe("Mystery Bowl", kcal=200, reliable=False, cuisine_id=cuisine)

    assert _rank(heavy, [thin]) == []


def test__unreliableBaseline__OffersNothingAtAll():
    cuisine = uuid4()
    _, heavy = _recipe("Carbonara", kcal=900, reliable=False, cuisine_id=cuisine)
    light = _recipe("Tray-bake", kcal=550, cuisine_id=cuisine)

    assert _rank(heavy, [light]) == []


def test__baselineWithNoFigure__OffersNothing():
    cuisine = uuid4()
    _, unknown = _recipe("Mystery", kcal=None, cuisine_id=cuisine)
    light = _recipe("Tray-bake", kcal=550, cuisine_id=cuisine)

    assert _rank(unknown, [light]) == []


def test__strangerRecipes__AreNeverPushed():
    # No affinity: not cookable, different style, never cooked. Same rule the
    # budget axis uses — a lighter meal nobody in the house eats isn't an answer.
    _, heavy = _recipe("Carbonara", kcal=900, cuisine_id=uuid4())
    stranger = _recipe("Natto Bowl", kcal=300, cuisine_id=uuid4())

    assert _rank(heavy, [stranger]) == []


def test__alreadyPlannedRecipes__AreSkipped():
    cuisine = uuid4()
    _, heavy = _recipe("Carbonara", kcal=900, cuisine_id=cuisine)
    planned_id, planned = _recipe("Tray-bake", kcal=550, cuisine_id=cuisine)

    assert _rank(heavy, [(planned_id, planned)], planned={planned_id}) == []


def test__ordering__BiggestReductionFirstThenAffinity():
    cuisine = uuid4()
    _, heavy = _recipe("Carbonara", kcal=900, cuisine_id=cuisine)
    small_win = _recipe("Pasta Bianca", kcal=800, cuisine_id=cuisine)
    big_win = _recipe("Broth", kcal=400, cuisine_id=cuisine)
    # Same reduction as big_win, but cookable right now — affinity breaks the tie.
    big_win_cookable = _recipe("Stir Fry", kcal=400, cookable=True, cuisine_id=cuisine)

    out = _rank(heavy, [small_win, big_win, big_win_cookable])

    assert [c.to_recipe_name for c in out] == ["Stir Fry", "Broth", "Pasta Bianca"]
    assert out[0].reason_chip == CHIP_LIGHTER_COOKABLE
    assert out[1].reason_chip == CHIP_LIGHTER_SIMILAR


def test__householdFavourite__QualifiesWhenNothingElseDoes():
    _, heavy = _recipe("Carbonara", kcal=900, cuisine_id=uuid4())
    cooked_before = _recipe("Soup", kcal=300, cuisine_id=uuid4(),
                            last_made_on="2026-07-01")

    out = _rank(heavy, [cooked_before])

    assert out[0].reason_chip == CHIP_LIGHTER_HOUSEHOLD_FAV


def test__candidateList__IsCappedSoTheDialogIsAChoiceNotAWall():
    cuisine = uuid4()
    _, heavy = _recipe("Carbonara", kcal=900, cuisine_id=cuisine)
    many = [_recipe(f"Light {i}", kcal=500 + i, cuisine_id=cuisine) for i in range(12)]

    assert len(_rank(heavy, many)) == MAX_LIGHTER_CANDIDATES
