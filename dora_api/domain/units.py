"""Canonical unit-conversion authority (FU-227 chunk 1).

The single server-side source of truth for measurement units, their aliases,
conversion factors, ingredient densities, and the gas-mark scale. Was inlined
in ``features/assistant/tools.py`` until the pricing reassessment exposed it
as a domain concept the price-entry widget, the harvest path, and the
assistant tool all need.

Six dimensions: ``volume`` (base ``ml``), ``mass`` (base ``g``), ``count``
(base ``ea`` — new per B1 for sizeless price entry), ``temperature`` (base
``°C``, handled with offsets out-of-band), ``length`` (base ``mm``),
``energy`` (base ``kJ``).

R-003: this module owns the table; nothing else may declare a unit factor or
density. The SPA mirror at ``web_app/src/generated/units_table.ts`` is
codegen'd from this file via ``scripts/dump_units.py`` — never hand-edited.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ── Dimensions ────────────────────────────────────────────────────────────

VOLUME = "volume"
MASS = "mass"
COUNT = "count"             # B1 — sizeless ("ea", "pack", "dozen").
TEMPERATURE = "temperature"
LENGTH = "length"
ENERGY = "energy"

# The dimensions a price observation may be expressed in. Volume + mass cover
# weighed/measured goods; count covers the sizeless "$9 for 3 punnets" case.
# Temperature/length/energy are recipe-side only and never appear on a price
# row (a charter call — observations are price records, not recipe records).
PRICE_DIMENSIONS = frozenset({VOLUME, MASS, COUNT})


# FU-227 chunk 4 — the **compute** denominator per dimension. Baseline math
# (`your_prices.py`) normalises every observation into one of these before
# computing the median, so the median is comparable across observations
# logged in different aliases (e.g. "L" + "ml" both land on "L"). The
# user-facing denominator may differ — see `display_denominator_for` below.
CANONICAL_PRICE_UNIT: dict[str, str] = {
    VOLUME: "L",
    MASS: "kg",
    COUNT: "ea",
}


SUPPORTED_PRICING_LOCALES: frozenset[str] = frozenset({"AU", "US"})


def display_denominator_for(
    active_dim: str,
    latest_measure_in_canonical: float,
    *,
    locale: str = "AU",
) -> tuple[str, float]:
    """The shelf display convention for a per-unit price.

    Returns ``(label, divide_factor)``: the user-facing denominator the
    widget renders (e.g. ``"L"`` / ``"100ml"`` for AU; ``"qt"`` / ``"fl oz"``
    for US) and the number by which a price computed in the dimension's
    :data:`CANONICAL_PRICE_UNIT` (compute unit) must be divided to land in
    that denominator.

    Size-aware: the flip kicks in only once the latest observation reaches a
    full target unit (≥ 1 L / ≥ 1 kg under AU; ≥ 1 qt / ≥ 1 lb under US).
    Below that, the convention is the smaller denominator
    ("$1.75 / 100ml" reads more naturally than "$17.50 / L" for a 500 ml
    bottle; same for "$0.50 / fl oz" vs "$16.00 / qt"). Count stays "ea"
    (no fractional convention either way).

    Locale is resolved server-side from ``AppSetting.unit_pricing_locale``
    — single source so the chart axis, sidecar entries, widget headline,
    and chart points all share one denominator. Compute math is locale-
    independent; only the rendered denominator changes.
    """
    if active_dim == COUNT:
        return ("ea", 1.0)
    if locale == "US":
        return _us_denominator(active_dim, latest_measure_in_canonical)
    # AU is the default for any unrecognised locale string — safe fallback.
    return _au_denominator(active_dim, latest_measure_in_canonical)


def _au_denominator(active_dim: str, measure_in_canonical: float) -> tuple[str, float]:
    if active_dim == VOLUME:
        if measure_in_canonical >= 1.0:
            return ("L", 1.0)
        return ("100ml", 10.0)
    # MASS
    if measure_in_canonical >= 1.0:
        return ("kg", 1.0)
    return ("100g", 10.0)


# US flip thresholds in the dimension's canonical unit:
#   1 qt = 0.946 L (volume canonical)
#   1 lb = 0.4536 kg (mass canonical)
# Divide factors precomputed from the conversion table so $/L → $/qt is
# `price / (qt-per-L)` = `price / 1.0567` ≈ `price × 0.946`.
_US_FLIP_QT_L = 0.946352946
_US_FLIP_LB_KG = 0.45359237
_US_FACTOR_QT = 1.0 / _US_FLIP_QT_L          # qt per L  ≈ 1.0567
_US_FACTOR_FL_OZ = 1000.0 / 29.5735           # fl oz per L  ≈ 33.8140
_US_FACTOR_LB = 1.0 / _US_FLIP_LB_KG          # lb per kg  ≈ 2.2046
_US_FACTOR_OZ = 1000.0 / 28.3495              # oz per kg  ≈ 35.2740


def _us_denominator(active_dim: str, measure_in_canonical: float) -> tuple[str, float]:
    if active_dim == VOLUME:
        # 1 qt = 0.946 L. At-or-above 1 qt → /qt; below → /fl oz.
        if measure_in_canonical >= _US_FLIP_QT_L:
            return ("qt", _US_FACTOR_QT)
        return ("fl oz", _US_FACTOR_FL_OZ)
    # MASS — 1 lb = 0.4536 kg.
    if measure_in_canonical >= _US_FLIP_LB_KG:
        return ("lb", _US_FACTOR_LB)
    return ("oz", _US_FACTOR_OZ)


# Practical price-entry picker whitelist. The conversion engine knows many
# more units (`cup` / `tsp` / `tbsp` / `pinch` / `dash` / `fl oz` / `pt` /
# `qt` / `gal` / `smidgen` / `stick`), but those are **cooking** units —
# nobody in AU buys oil by the cup or eggs by the pinch. The picker shows
# only what people actually shop in. The server still ACCEPTS the broader
# set (the harvest path may see a sized product in `cup` or `fl oz`), so
# this is purely a UI narrowing, not a validation tightening.
PRICE_PICKER_CANONICAL_UNITS: frozenset[str] = frozenset({
    # volume
    "ml", "L",
    # mass — practical AU + imperial for meat/cheese
    "g", "kg", "oz", "lb",
    # count
    "ea", "dozen", "pack",
})


# ── Unit table ────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class UnitDef:
    """One row in :data:`UNIT_TABLE`. ``factor`` converts an amount in this
    unit to the dimension's base unit (ml / g / ea / mm / kJ; temperature is
    offset-based so its factor is the linear scale only)."""
    dimension: str
    factor: float
    canonical: str          # the preferred display alias for this unit


# Every alias keys an entry. ``canonical`` is the same string for every alias
# of a single unit so the SPA picker can group/dedupe. Aussie-metric defaults
# (250 ml cup, 20 ml tbsp); US cup/tbsp explicitly distinct.
UNIT_TABLE: dict[str, UnitDef] = {
    # ── Volume — base ml ──────────────────────────────────────────────
    "ml": UnitDef(VOLUME, 1.0, "ml"),
    "milliliter": UnitDef(VOLUME, 1.0, "ml"),
    "millilitre": UnitDef(VOLUME, 1.0, "ml"),
    "milliliters": UnitDef(VOLUME, 1.0, "ml"),
    "millilitres": UnitDef(VOLUME, 1.0, "ml"),
    "l": UnitDef(VOLUME, 1000.0, "L"),
    "litre": UnitDef(VOLUME, 1000.0, "L"),
    "liter": UnitDef(VOLUME, 1000.0, "L"),
    "litres": UnitDef(VOLUME, 1000.0, "L"),
    "liters": UnitDef(VOLUME, 1000.0, "L"),
    "smidgen": UnitDef(VOLUME, 0.156, "smidgen"),
    "smidge": UnitDef(VOLUME, 0.156, "smidgen"),
    "pinch": UnitDef(VOLUME, 0.3125, "pinch"),
    "pinches": UnitDef(VOLUME, 0.3125, "pinch"),
    "dash": UnitDef(VOLUME, 0.625, "dash"),
    "dashes": UnitDef(VOLUME, 0.625, "dash"),
    "tsp": UnitDef(VOLUME, 5.0, "tsp"),
    "teaspoon": UnitDef(VOLUME, 5.0, "tsp"),
    "teaspoons": UnitDef(VOLUME, 5.0, "tsp"),
    "tbsp": UnitDef(VOLUME, 20.0, "tbsp"),          # AU metric (20 ml)
    "tablespoon": UnitDef(VOLUME, 20.0, "tbsp"),
    "tablespoons": UnitDef(VOLUME, 20.0, "tbsp"),
    "us tbsp": UnitDef(VOLUME, 14.7868, "US tbsp"),
    "american tbsp": UnitDef(VOLUME, 14.7868, "US tbsp"),
    "us tablespoon": UnitDef(VOLUME, 14.7868, "US tbsp"),
    "cup": UnitDef(VOLUME, 250.0, "cup"),            # AU metric (250 ml)
    "cups": UnitDef(VOLUME, 250.0, "cup"),
    "us cup": UnitDef(VOLUME, 240.0, "US cup"),
    "us cups": UnitDef(VOLUME, 240.0, "US cup"),
    "american cup": UnitDef(VOLUME, 240.0, "US cup"),
    "american cups": UnitDef(VOLUME, 240.0, "US cup"),
    "fl oz": UnitDef(VOLUME, 29.5735, "fl oz"),
    "floz": UnitDef(VOLUME, 29.5735, "fl oz"),
    "fluid ounce": UnitDef(VOLUME, 29.5735, "fl oz"),
    "fluid ounces": UnitDef(VOLUME, 29.5735, "fl oz"),
    "pint": UnitDef(VOLUME, 568.261, "pt"),          # UK
    "pints": UnitDef(VOLUME, 568.261, "pt"),
    "pt": UnitDef(VOLUME, 568.261, "pt"),
    "quart": UnitDef(VOLUME, 946.353, "qt"),         # US
    "quarts": UnitDef(VOLUME, 946.353, "qt"),
    "qt": UnitDef(VOLUME, 946.353, "qt"),
    "gallon": UnitDef(VOLUME, 3785.41, "gal"),
    "gallons": UnitDef(VOLUME, 3785.41, "gal"),
    "gal": UnitDef(VOLUME, 3785.41, "gal"),

    # ── Mass — base g ─────────────────────────────────────────────────
    "mg": UnitDef(MASS, 0.001, "mg"),
    "milligram": UnitDef(MASS, 0.001, "mg"),
    "milligrams": UnitDef(MASS, 0.001, "mg"),
    "g": UnitDef(MASS, 1.0, "g"),
    "gm": UnitDef(MASS, 1.0, "g"),
    "gram": UnitDef(MASS, 1.0, "g"),
    "grams": UnitDef(MASS, 1.0, "g"),
    "kg": UnitDef(MASS, 1000.0, "kg"),
    "kilo": UnitDef(MASS, 1000.0, "kg"),
    "kilos": UnitDef(MASS, 1000.0, "kg"),
    "kilogram": UnitDef(MASS, 1000.0, "kg"),
    "kilograms": UnitDef(MASS, 1000.0, "kg"),
    "oz": UnitDef(MASS, 28.3495, "oz"),
    "ounce": UnitDef(MASS, 28.3495, "oz"),
    "ounces": UnitDef(MASS, 28.3495, "oz"),
    "lb": UnitDef(MASS, 453.592, "lb"),
    "lbs": UnitDef(MASS, 453.592, "lb"),
    "pound": UnitDef(MASS, 453.592, "lb"),
    "pounds": UnitDef(MASS, 453.592, "lb"),
    "stick": UnitDef(MASS, 113.0, "stick"),          # butter
    "sticks": UnitDef(MASS, 113.0, "stick"),

    # ── Count — base ea (new — B1, FU-227) ────────────────────────────
    # "pack" is a placeholder: long-term a pack is N items, but without a
    # per-product pack size we can't know N (see plan §7 / Risk). For now
    # a pack means "the thing the price is per" with factor 1, identical
    # to ea — explicit aliasing for UI clarity, not different math.
    "ea": UnitDef(COUNT, 1.0, "ea"),
    "each": UnitDef(COUNT, 1.0, "ea"),
    "unit": UnitDef(COUNT, 1.0, "ea"),
    "units": UnitDef(COUNT, 1.0, "ea"),
    "pack": UnitDef(COUNT, 1.0, "pack"),
    "packs": UnitDef(COUNT, 1.0, "pack"),
    "dozen": UnitDef(COUNT, 12.0, "dozen"),
    "dozens": UnitDef(COUNT, 12.0, "dozen"),

    # ── Length — base mm ──────────────────────────────────────────────
    "mm": UnitDef(LENGTH, 1.0, "mm"),
    "millimeter": UnitDef(LENGTH, 1.0, "mm"),
    "millimetre": UnitDef(LENGTH, 1.0, "mm"),
    "millimeters": UnitDef(LENGTH, 1.0, "mm"),
    "millimetres": UnitDef(LENGTH, 1.0, "mm"),
    "cm": UnitDef(LENGTH, 10.0, "cm"),
    "centimeter": UnitDef(LENGTH, 10.0, "cm"),
    "centimetre": UnitDef(LENGTH, 10.0, "cm"),
    "centimeters": UnitDef(LENGTH, 10.0, "cm"),
    "centimetres": UnitDef(LENGTH, 10.0, "cm"),
    "m": UnitDef(LENGTH, 1000.0, "m"),
    "meter": UnitDef(LENGTH, 1000.0, "m"),
    "metre": UnitDef(LENGTH, 1000.0, "m"),
    "meters": UnitDef(LENGTH, 1000.0, "m"),
    "metres": UnitDef(LENGTH, 1000.0, "m"),
    "in": UnitDef(LENGTH, 25.4, "in"),
    "inch": UnitDef(LENGTH, 25.4, "in"),
    "inches": UnitDef(LENGTH, 25.4, "in"),
    '"': UnitDef(LENGTH, 25.4, "in"),
    "ft": UnitDef(LENGTH, 304.8, "ft"),
    "foot": UnitDef(LENGTH, 304.8, "ft"),
    "feet": UnitDef(LENGTH, 304.8, "ft"),

    # ── Energy — base kJ (AU nutrition labels show both) ──────────────
    "kj": UnitDef(ENERGY, 1.0, "kJ"),
    "kilojoule": UnitDef(ENERGY, 1.0, "kJ"),
    "kilojoules": UnitDef(ENERGY, 1.0, "kJ"),
    "kcal": UnitDef(ENERGY, 4.184, "kcal"),
    "cal": UnitDef(ENERGY, 4.184, "kcal"),
    "calorie": UnitDef(ENERGY, 4.184, "kcal"),
    "calories": UnitDef(ENERGY, 4.184, "kcal"),
    "j": UnitDef(ENERGY, 0.001, "J"),
    "joule": UnitDef(ENERGY, 0.001, "J"),
    "joules": UnitDef(ENERGY, 0.001, "J"),
}


# Grams per millilitre. Cross-dimension mass↔volume needs this; without an
# ingredient hint the cross-dimension call fails cleanly.
INGREDIENT_DENSITY_G_PER_ML: dict[str, float] = {
    # Liquids
    "water": 1.00, "milk": 1.03,
    "olive oil": 0.92, "oil": 0.92, "vegetable oil": 0.92, "canola oil": 0.92,
    "honey": 1.42, "maple syrup": 1.32, "golden syrup": 1.40,
    # Flours
    "flour": 0.53, "plain flour": 0.53,
    "all-purpose flour": 0.53, "all purpose flour": 0.53,
    "self-raising flour": 0.53, "self raising flour": 0.53,
    "wholemeal flour": 0.56, "whole wheat flour": 0.56, "bread flour": 0.55,
    "almond flour": 0.42, "almond meal": 0.42,
    # Sugars
    "sugar": 0.85, "white sugar": 0.85, "caster sugar": 0.85, "granulated sugar": 0.85,
    "brown sugar": 0.93,
    "icing sugar": 0.56, "powdered sugar": 0.56, "confectioners sugar": 0.56,
    # Fats / dairy
    "butter": 0.91, "margarine": 0.91,
    "yogurt": 1.04, "greek yogurt": 1.05,
    "sour cream": 0.95, "cream cheese": 0.95, "ricotta": 0.85, "mascarpone": 1.00,
    "cream": 1.00, "heavy cream": 1.00, "thickened cream": 1.00,
    "peanut butter": 1.05,
    # Grains / pulses / starches
    "rice": 0.78, "white rice": 0.78, "brown rice": 0.76,
    "rolled oats": 0.41, "oats": 0.41, "porridge oats": 0.41,
    "quinoa": 0.72, "couscous": 0.72,
    "dried lentils": 0.85, "lentils": 0.85,
    "dried beans": 0.85, "chickpeas": 0.78,
    "pasta": 0.50, "dry pasta": 0.50,
    "cornstarch": 0.65, "cornflour": 0.65,
    # Bakery / nuts / dried
    "chocolate chips": 0.65, "chocolate": 0.62,
    "chopped almonds": 0.50, "sliced almonds": 0.45, "whole almonds": 0.60,
    "chopped walnuts": 0.55, "walnuts": 0.55,
    "raisins": 0.65, "sultanas": 0.65,
    "shredded coconut": 0.30, "desiccated coconut": 0.45,
    "breadcrumbs": 0.45, "panko": 0.30,
    "cocoa powder": 0.51, "cocoa": 0.51,
    "salt": 1.20,
    # Cheese (grated)
    "parmesan": 0.45, "grated parmesan": 0.45,
    "cheddar": 0.48, "grated cheddar": 0.48, "grated cheese": 0.48,
}


# Gas mark ↔ °C — non-linear UK oven scale. "Gas mark 6" means 200 °C; for
# the reverse we snap to the nearest entry.
GAS_MARK_TO_C: dict[str, float] = {
    "1/4": 110, "1/2": 120, "1": 140, "2": 150, "3": 160, "4": 180,
    "5": 190, "6": 200, "7": 220, "8": 230, "9": 240,
}
GAS_MARK_ALIASES = frozenset({"gas", "gas mark", "gm"})


# ── Helpers ───────────────────────────────────────────────────────────────


def normalise_unit(unit: str) -> str:
    """Lowercase + strip whitespace + strip degree marks. Use before any
    :data:`UNIT_TABLE` lookup so "L", " L", "°C" all collapse correctly."""
    return unit.strip().lower().replace("°", "")


def find_unit(unit: str) -> UnitDef | None:
    """Return the :class:`UnitDef` for *unit* or None. Plural fallback: ``cups``
    is in the table directly; for one-off plurals not enumerated we'd strip
    trailing ``s`` — but we list common plurals exhaustively above to avoid
    swallowing units that legitimately end in s (e.g. ``oz``)."""
    norm = normalise_unit(unit)
    return UNIT_TABLE.get(norm)


def dimension_of(unit: str) -> str | None:
    """Convenience: the dimension string for *unit*, or None if unknown."""
    found = find_unit(unit)
    return found.dimension if found else None


def parse_amount(raw: Any) -> float | None:
    """Accept 1, 1.5, "1/2", "1 1/2" — fractions and mixed numbers fall out
    of LLM tool calls more often than clean floats, so handle them here."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip()
    if not s:
        return None
    # Mixed: "1 1/2"
    parts = s.split()
    if len(parts) == 2 and "/" in parts[1]:
        try:
            whole = float(parts[0])
            num, den = parts[1].split("/")
            denom = float(den)
            if not denom:
                return None
            frac = float(num) / denom
            return whole - frac if whole < 0 else whole + frac
        except ValueError:
            return None
    # Pure fraction
    if "/" in s:
        try:
            num, den = s.split("/")
            denom = float(den)
            if not denom:
                return None
            return float(num) / denom
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def snap_gas_mark(celsius: float) -> str:
    """Nearest gas-mark string for *celsius*."""
    best_key, best_delta = "4", float("inf")
    for key, val in GAS_MARK_TO_C.items():
        delta = abs(val - celsius)
        if delta < best_delta:
            best_key, best_delta = key, delta
    return best_key


def convert(
    amount: float,
    from_unit: str,
    to_unit: str,
    *,
    ingredient: str | None = None,
) -> float | None:
    """Linear conversion within one dimension; cross-dimension mass↔volume
    when *ingredient* (lowercase) maps to a known density. Returns None when
    the units are unknown or the dimensions can't bridge — callers handle
    the error shape themselves.

    Temperature and gas mark are handled by :func:`convert_temperature` /
    :func:`convert_gas_mark` (offsets + non-linear; would muddy this
    function's contract)."""
    src = find_unit(from_unit)
    dst = find_unit(to_unit)
    if not src or not dst:
        return None
    if src.dimension == dst.dimension:
        return amount * src.factor / dst.factor
    if {src.dimension, dst.dimension} == {MASS, VOLUME}:
        if not ingredient:
            return None
        density = INGREDIENT_DENSITY_G_PER_ML.get(ingredient.lower())
        if density is None:
            return None
        base = amount * src.factor                # to source's base unit
        if src.dimension == MASS:                 # g → ml via density
            ml = base / density
            return ml / dst.factor
        grams = base * density                    # ml → g via density
        return grams / dst.factor
    return None


def convert_temperature(amount: float, from_unit: str, to_unit: str) -> float | None:
    """C/F/K with offsets. Returns None if either side isn't a temperature."""
    temp = {"c", "celsius", "celcius", "f", "fahrenheit", "k", "kelvin"}
    f, t = normalise_unit(from_unit), normalise_unit(to_unit)
    if f not in temp or t not in temp:
        return None

    def to_c(v: float, u: str) -> float:
        if u in ("c", "celsius", "celcius"):
            return v
        if u in ("f", "fahrenheit"):
            return (v - 32) * 5 / 9
        return v - 273.15  # kelvin

    def from_c(v: float, u: str) -> float:
        if u in ("c", "celsius", "celcius"):
            return v
        if u in ("f", "fahrenheit"):
            return v * 9 / 5 + 32
        return v + 273.15

    return from_c(to_c(amount, f), t)


def is_gas_mark_alias(token: str) -> bool:
    return normalise_unit(token) in GAS_MARK_ALIASES


# ── Price-entry convenience (chunk 3 / B3) ────────────────────────────────


@dataclass(frozen=True, slots=True)
class CanonicalUnitChoice:
    """One picker row for the price-entry widget. ``canonical`` is the
    persisted string; ``label`` is the display string."""
    canonical: str
    label: str
    dimension: str


def supported_price_units() -> list[CanonicalUnitChoice]:
    """Flat global list of units the price-entry widget offers (B3),
    grouped client-side by dimension. The cooking-only units (cup, tsp,
    tbsp, pinch, dash, fl oz, pt, qt, gal, smidgen, stick) are filtered out
    via :data:`PRICE_PICKER_CANONICAL_UNITS` — the conversion engine still
    knows them for the assistant and the harvest path, but the picker
    shows only what AU shoppers actually shop in."""
    seen: dict[str, CanonicalUnitChoice] = {}
    for udef in UNIT_TABLE.values():
        if udef.dimension not in PRICE_DIMENSIONS:
            continue
        if udef.canonical not in PRICE_PICKER_CANONICAL_UNITS:
            continue
        if udef.canonical in seen:
            continue
        seen[udef.canonical] = CanonicalUnitChoice(
            canonical=udef.canonical,
            label=udef.canonical,
            dimension=udef.dimension,
        )
    return list(seen.values())
