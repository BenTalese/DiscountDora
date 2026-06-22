"""FU-227 chunk 5 — the shared shopping-line price helpers.

Pure-function coverage for `_line_price.line_paid_unit_price` (the actual→picked
ladder, K2 extract) and `harvest_observation_fields` (the E4 measure-vs-count
fold). No server needed — these are the chokepoints the /finish harvest, the
budget/waste/assistant reports and the dev seed all share.
"""
from uuid import uuid4

from dora_api.domain.entities.shopping_list import ShoppingListLine
from dora_api.features.shopping_lists._line_price import (
    harvest_observation_fields, line_paid_unit_price)


def _line(*, actual=None, picked=None, quantity=1) -> ShoppingListLine:
    return ShoppingListLine(
        shopping_list_id=uuid4(),
        actual_unit_price=actual,
        picked_offer_price=picked,
        quantity=quantity,
    )


# ── line_paid_unit_price — the ladder ─────────────────────────────────────

def test__ladder__actual_wins_over_picked():
    assert line_paid_unit_price(_line(actual=1.5, picked=2.0)) == 1.5


def test__ladder__falls_back_to_picked():
    assert line_paid_unit_price(_line(actual=None, picked=2.0)) == 2.0


def test__ladder__none_when_neither_set():
    assert line_paid_unit_price(_line(actual=None, picked=None)) is None


# ── harvest_observation_fields — E4 measure vs count ──────────────────────

def test__harvest__sized_volume_product_is_measure_obs():
    # 2 bottles of 2 L at $4/bottle → $8 total for 4 L.
    tp, tm, unit, _pc = harvest_observation_fields(
        unit_price=4.0, quantity=2, size_value=2.0, size_unit="L")
    assert (tp, tm, unit) == (8.0, 4.0, "L")


def test__harvest__sized_mass_product_canonicalises_unit():
    # size_unit alias persists as its canonical form (g stays g).
    tp, tm, unit, _pc = harvest_observation_fields(
        unit_price=1.30, quantity=1, size_value=500.0, size_unit="grams")
    assert tp == 1.30 and tm == 500.0 and unit == "g"


def test__harvest__sizeless_line_is_count_obs():
    # No product → one "ea" per item; total_price = unit_price × qty.
    tp, tm, unit, _pc = harvest_observation_fields(
        unit_price=6.0, quantity=3, size_value=None, size_unit=None)
    assert (tp, tm, unit) == (18.0, 3.0, "ea")


def test__harvest__count_dimension_product_keeps_measure():
    # A "12 ea" carton bought ×2 → 24 ea, price × 2.
    tp, tm, unit, _pc = harvest_observation_fields(
        unit_price=7.5, quantity=2, size_value=12.0, size_unit="ea")
    assert (tp, tm, unit) == (15.0, 24.0, "ea")


def test__harvest__unsupported_size_unit_falls_back_to_count():
    # A length unit isn't a price dimension → count obs, not a measure obs.
    tp, tm, unit, _pc = harvest_observation_fields(
        unit_price=2.0, quantity=1, size_value=10.0, size_unit="cm")
    assert (tp, tm, unit) == (2.0, 1.0, "ea")


def test__harvest__zero_size_value_falls_back_to_count():
    tp, tm, unit, _pc = harvest_observation_fields(
        unit_price=2.0, quantity=1, size_value=0.0, size_unit="L")
    assert (tp, tm, unit) == (2.0, 1.0, "ea")


def test__harvest__none_quantity_defaults_to_one():
    tp, tm, unit, _pc = harvest_observation_fields(
        unit_price=5.0, quantity=None, size_value=None, size_unit=None)
    assert (tp, tm, unit) == (5.0, 1.0, "ea")
