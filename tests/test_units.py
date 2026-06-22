"""Unit tests for the canonical unit-conversion authority
(``dora_api.domain.units``).

R-003: this module owns the unit table; nothing else may redeclare it. Tests
pin (a) within-dimension linearity, (b) cross-dimension mass↔volume via
ingredient density, (c) the new count dimension (B1 / FU-227), and (d) the
gas-mark + temperature offsets that live outside the linear table.
"""
import math

import pytest

from dora_api.domain import units


# ── Within-dimension linear conversion ────────────────────────────────────


@pytest.mark.parametrize(
    "amount,from_unit,to_unit,expected",
    [
        (1, "L", "ml", 1000.0),
        (500, "ml", "L", 0.5),
        (1, "cup", "ml", 250.0),       # AU metric cup
        (1, "us cup", "ml", 240.0),    # explicitly distinct
        (1, "kg", "g", 1000.0),
        (1000, "mg", "g", 1.0),
        (1, "lb", "g", 453.592),
        (1, "tbsp", "tsp", 4.0),       # 20 ml / 5 ml — AU metric
    ],
)
def test__convert_within_dimension(amount, from_unit, to_unit, expected):
    result = units.convert(amount, from_unit, to_unit)
    assert result is not None
    assert math.isclose(result, expected, rel_tol=1e-6)


# ── Count dimension (new in FU-227) ───────────────────────────────────────


def test__count_dimension_dozen_to_each():
    assert units.convert(2, "dozen", "ea") == 24.0


def test__count_dimension_each_to_dozen():
    assert units.convert(24, "ea", "dozen") == 2.0


def test__count_dimension_pack_factor_is_one():
    # See domain/units.py: "pack" is a placeholder — same as ea — until a
    # per-product pack-size lookup lands. This test pins the placeholder so
    # a future change is explicit.
    assert units.convert(1, "pack", "ea") == 1.0


def test__count_dimension_does_not_bridge_to_volume():
    """No cross-dimension conversion ea↔L (count has no density)."""
    assert units.convert(1, "ea", "L") is None
    assert units.convert(1, "L", "ea") is None


def test__count_dimension_does_not_bridge_to_mass():
    assert units.convert(1, "ea", "g") is None


def test__count_dimension_listed_in_supported_price_units():
    canon = {u.canonical for u in units.supported_price_units()}
    assert "ea" in canon
    assert "dozen" in canon
    assert "pack" in canon


# ── Cross-dimension mass↔volume via ingredient density ────────────────────


def test__cross_dimension_cup_flour_to_grams():
    """1 cup (250 ml) × density 0.53 g/ml = 132.5 g."""
    result = units.convert(1, "cup", "g", ingredient="flour")
    assert result is not None
    assert math.isclose(result, 132.5, rel_tol=1e-6)


def test__cross_dimension_grams_to_ml_with_density():
    """100 g of water / density 1.00 g/ml = 100 ml."""
    result = units.convert(100, "g", "ml", ingredient="water")
    assert result is not None
    assert math.isclose(result, 100.0, rel_tol=1e-6)


def test__cross_dimension_without_ingredient_returns_none():
    assert units.convert(1, "cup", "g") is None


def test__cross_dimension_with_unknown_ingredient_returns_none():
    assert units.convert(1, "cup", "g", ingredient="unobtanium") is None


# ── Unknown unit handling ─────────────────────────────────────────────────


def test__convert_unknown_unit_returns_none():
    assert units.convert(1, "smoots", "ml") is None
    assert units.convert(1, "ml", "smoots") is None


# ── normalise_unit / find_unit ────────────────────────────────────────────


@pytest.mark.parametrize("raw,expected", [
    ("L", "l"),
    (" L ", "l"),
    ("°C", "c"),
    ("LITRES", "litres"),
])
def test__normalise_unit_strips_whitespace_lowercases_strips_degree(raw, expected):
    assert units.normalise_unit(raw) == expected


def test__find_unit_resolves_plurals_listed_explicitly():
    assert units.find_unit("litres").dimension == units.VOLUME
    assert units.find_unit("grams").dimension == units.MASS
    assert units.find_unit("dozens").dimension == units.COUNT


def test__find_unit_unknown_returns_none():
    assert units.find_unit("smoots") is None


# ── Temperature (offsets — lives outside the linear table) ────────────────


def test__temperature_c_to_f():
    assert math.isclose(units.convert_temperature(100, "c", "f"), 212.0, rel_tol=1e-9)


def test__temperature_f_to_c():
    assert math.isclose(units.convert_temperature(32, "f", "c"), 0.0, abs_tol=1e-9)


def test__temperature_celcius_misspelling_still_works():
    """Common misspelling — kept as an alias on purpose; pin it."""
    assert math.isclose(units.convert_temperature(0, "celcius", "f"), 32.0, abs_tol=1e-9)


def test__temperature_non_temp_unit_returns_none():
    assert units.convert_temperature(1, "ml", "c") is None


# ── Gas mark snap ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("celsius,expected", [
    (200, "6"),
    (180, "4"),
    (140, "1"),
    (240, "9"),
    (110, "1/4"),
])
def test__snap_gas_mark(celsius, expected):
    assert units.snap_gas_mark(celsius) == expected


# ── parse_amount ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("raw,expected", [
    (1, 1.0),
    (1.5, 1.5),
    ("1", 1.0),
    ("1.5", 1.5),
    ("1/2", 0.5),
    ("1 1/2", 1.5),
    ("3/4", 0.75),
])
def test__parse_amount_accepts_fractions_and_mixed(raw, expected):
    assert units.parse_amount(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "  ", "abc", "1/0", "1 1/0"])
def test__parse_amount_returns_none_on_bad_input(raw):
    assert units.parse_amount(raw) is None


# ── Price-restricted dimension set (B3 picker) ────────────────────────────


def test__supported_price_units_restricted_to_volume_mass_count():
    """The price-entry widget never offers temperature / length / energy."""
    rows = units.supported_price_units()
    assert all(r.dimension in {units.VOLUME, units.MASS, units.COUNT} for r in rows)


def test__supported_price_units_no_duplicate_canonicals():
    rows = units.supported_price_units()
    canon = [r.canonical for r in rows]
    assert len(canon) == len(set(canon))
