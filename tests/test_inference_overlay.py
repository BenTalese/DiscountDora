"""FU-653 — the belief overlay's decision rules.

`recipe_hint` is the one place that decides whether Dora says anything about a
recipe, so it's pinned here: it's a pure function over rows + a precomputed
divergence, it's cheap to test, and it encodes a promise the owner made
explicitly ("this must not change cookability, and it must stay quiet unless
it's actually adding something"). That's exactly the stable, low-churn contract
the verification stance says to automate.

The belief *engine* itself is tested in `test_pantry_belief.py`; nothing here
re-tests inference maths.
"""
from uuid import uuid4

import pytest

from dora_api.features.stock_items.inference_overlay import (
    EMPTY_DIVERGENCE, HINT_AT_RISK, HINT_MAYBE_COOKABLE, DivergentItems,
    IngredientRow, recipe_hint, surface_enabled,
)


pytestmark = pytest.mark.unit


FLOUR, EGGS, MILK = uuid4(), uuid4(), uuid4()


def _row(item_id, name, *, optional=False, missing=False):
    return IngredientRow(
        stock_item_id=item_id, name=name, is_optional=optional, is_missing=missing,
    )


def _divergence(*, out=(), available=()):
    return DivergentItems(
        believed_out=frozenset(out),
        believed_available=frozenset(available),
        reasons={},
    )


# ── at_risk: reads cookable, belief disagrees ────────────────────────────

def test__recipe_hint__cookable_recipe_with_believed_out_ingredient__at_risk():
    rows = [_row(FLOUR, "Flour"), _row(EGGS, "Eggs")]
    hint = recipe_hint(
        rows, _divergence(out=[EGGS]), missing_count=0, unlinked_count=0,
    )
    assert hint is not None
    assert hint.kind == HINT_AT_RISK
    assert hint.stock_item_names == ["Eggs"]


def test__recipe_hint__believed_out_ingredient_is_optional__stays_quiet():
    """Optional ingredients don't gate cookability, so they can't put a recipe
    at risk either — the overlay follows the same §1.9 rule as the count."""
    rows = [_row(FLOUR, "Flour"), _row(EGGS, "Eggs", optional=True)]
    assert recipe_hint(
        rows, _divergence(out=[EGGS]), missing_count=0, unlinked_count=0,
    ) is None


def test__recipe_hint__same_item_on_two_rows__named_once():
    rows = [_row(EGGS, "Eggs"), _row(EGGS, "Eggs")]
    hint = recipe_hint(
        rows, _divergence(out=[EGGS]), missing_count=0, unlinked_count=0,
    )
    assert hint is not None and hint.stock_item_names == ["Eggs"]


# ── maybe_cookable: reads not-cookable, belief disagrees ─────────────────

def test__recipe_hint__all_missing_believed_back_in_stock__maybe_cookable():
    rows = [_row(FLOUR, "Flour"), _row(EGGS, "Eggs", missing=True)]
    hint = recipe_hint(
        rows, _divergence(available=[EGGS]), missing_count=1, unlinked_count=0,
    )
    assert hint is not None
    assert hint.kind == HINT_MAYBE_COOKABLE
    assert hint.stock_item_names == ["Eggs"]


def test__recipe_hint__only_some_missing_rescued__stays_quiet():
    """Rescuing one of two missing ingredients still leaves you unable to cook
    it — saying "maybe you can" there would be a lie of omission."""
    rows = [
        _row(EGGS, "Eggs", missing=True),
        _row(MILK, "Milk", missing=True),
    ]
    assert recipe_hint(
        rows, _divergence(available=[EGGS]), missing_count=2, unlinked_count=0,
    ) is None


# ── the quiet cases ──────────────────────────────────────────────────────

def test__recipe_hint__no_divergence__returns_none():
    rows = [_row(FLOUR, "Flour")]
    assert recipe_hint(
        rows, EMPTY_DIVERGENCE, missing_count=0, unlinked_count=0,
    ) is None


def test__recipe_hint__unlinked_required_ingredient__returns_none():
    """Recorded cookability is already the honest None; a guess on top of an
    admitted unknown is worse than silence."""
    rows = [_row(FLOUR, "Flour"), _row(None, "1 cup of something")]
    assert recipe_hint(
        rows, _divergence(out=[FLOUR]), missing_count=0, unlinked_count=1,
    ) is None


def test__recipe_hint__recipe_with_no_linked_ingredients__returns_none():
    assert recipe_hint(
        [], _divergence(out=[FLOUR]), missing_count=0, unlinked_count=0,
    ) is None


# ── per-surface gate ─────────────────────────────────────────────────────

class _User:
    inferred_pantry_enabled = True
    inference_recipes_enabled = True
    inference_shopping_enabled = False
    inference_meal_plan_enabled = False


def test__surface_enabled__reads_the_surfaces_own_flag():
    user = _User()
    assert surface_enabled(user, "stock") is True
    assert surface_enabled(user, "recipes") is True
    assert surface_enabled(user, "shopping") is False
    assert surface_enabled(user, "meal_plan") is False


def test__surface_enabled__no_user_or_unknown_surface__false():
    assert surface_enabled(None, "recipes") is False
    assert surface_enabled(_User(), "not_a_surface") is False
