"""Regenerate ``web_app/src/generated/units_table.ts`` from the Python source
of truth at ``dora_api/domain/units.py`` (R-003 / B2).

Run from repo root: ``python scripts/dump_units.py``

The output file is checked in — this script only runs when the Python tables
change. CI may diff the output to catch unsynchronised edits.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dora_api.domain import units  # noqa: E402


HEADER = """// THIS FILE IS GENERATED — DO NOT EDIT BY HAND.
// Source of truth: dora_api/domain/units.py
// Regenerate via: python scripts/dump_units.py
//
// Mirror of the server-side unit-conversion table for the offline assistant
// rule-engine fallback (web_app/src/services/doraIntents.ts) and the
// price-entry widget's instant validation (web_app/src/components/dora/
// PriceEntry.vue). R-003: nothing here is hand-maintained.

"""

DIMENSIONS_TS = """export type Dimension =
    | 'volume'
    | 'mass'
    | 'count'
    | 'temperature'
    | 'length'
    | 'energy';

export const PRICE_DIMENSIONS: ReadonlyArray<Dimension> = ['volume', 'mass', 'count'];

export interface UnitDef {
    /** Dimension the unit belongs to. */
    readonly dimension: Dimension;
    /** Multiplier to the dimension's base unit (ml / g / ea / mm / kJ). */
    readonly factor: number;
    /** Preferred display string (e.g. "L" for "litre"). */
    readonly canonical: string;
}

"""


def _ts_string(s: str) -> str:
    return json.dumps(s)


def _emit_unit_table() -> str:
    lines = ["export const UNIT_TABLE: Readonly<Record<string, UnitDef>> = {"]
    for alias, udef in units.UNIT_TABLE.items():
        lines.append(
            f"    {_ts_string(alias)}: {{ dimension: {_ts_string(udef.dimension)}, "
            f"factor: {udef.factor!r}, canonical: {_ts_string(udef.canonical)} }},"
        )
    lines.append("};")
    lines.append("")
    return "\n".join(lines)


def _emit_measurement_systems() -> str:
    """The metric / imperial / US axis, keyed by canonical unit.

    The SPA needs it to narrow every unit dropdown to the install's chosen
    system (owner feedback 2026-08-27). Emitted rather than restated on the
    client for the same R-003 reason the conversion table is: one source, in
    `dora_api/domain/units.py`.
    """
    lines = [
        "export type MeasurementSystem = 'metric' | 'imperial' | 'us';",
        "",
        "export const MEASUREMENT_SYSTEMS: ReadonlyArray<MeasurementSystem> = ["
        + ", ".join(
            _ts_string(x)
            for x in ("metric", "imperial", "us")
        )
        + "];",
        "",
        "/** Canonical units that belong to every system — the informal cooking",
        " *  amounts, the count units, and energy. Always offered. */",
        "export const UNIVERSAL_CANONICAL_UNITS: ReadonlySet<string> = new Set(["
        + ", ".join(
            _ts_string(u) for u in sorted(units.UNIVERSAL_CANONICAL_UNITS)
        )
        + "]);",
        "",
        "/** Canonical unit → the systems that offer it. Units absent from both",
        " *  this map and `UNIVERSAL_CANONICAL_UNITS` are offered by no system. */",
        "export const UNIT_SYSTEMS: Readonly<Record<string, ReadonlyArray<MeasurementSystem>>> = {",
    ]
    for canonical, systems in units.UNIT_SYSTEMS.items():
        joined = ", ".join(_ts_string(x) for x in sorted(systems))
        lines.append(f"    {_ts_string(canonical)}: [{joined}],")
    lines.append("};")
    lines.append("")
    return "\n".join(lines)


def _emit_density_table() -> str:
    lines = ["export const INGREDIENT_DENSITY_G_PER_ML: Readonly<Record<string, number>> = {"]
    for name, density in units.INGREDIENT_DENSITY_G_PER_ML.items():
        lines.append(f"    {_ts_string(name)}: {density!r},")
    lines.append("};")
    lines.append("")
    return "\n".join(lines)


def _emit_gas_mark() -> str:
    lines = ["export const GAS_MARK_TO_C: Readonly<Record<string, number>> = {"]
    for key, val in units.GAS_MARK_TO_C.items():
        lines.append(f"    {_ts_string(key)}: {val!r},")
    lines.append("};")
    lines.append("")
    lines.append(
        "export const GAS_MARK_ALIASES: ReadonlySet<string> = new Set(["
        + ", ".join(_ts_string(a) for a in sorted(units.GAS_MARK_ALIASES))
        + "]);"
    )
    lines.append("")
    return "\n".join(lines)


def _emit_supported_price_units() -> str:
    rows = units.supported_price_units()
    lines = [
        "export interface CanonicalUnitChoice {",
        "    readonly canonical: string;",
        "    readonly label: string;",
        "    readonly dimension: Dimension;",
        "}",
        "",
        "export const SUPPORTED_PRICE_UNITS: ReadonlyArray<CanonicalUnitChoice> = [",
    ]
    for row in rows:
        lines.append(
            f"    {{ canonical: {_ts_string(row.canonical)}, "
            f"label: {_ts_string(row.label)}, dimension: {_ts_string(row.dimension)} }},"
        )
    lines.append("];")
    lines.append("")
    return "\n".join(lines)


def render() -> str:
    parts = [
        HEADER,
        DIMENSIONS_TS,
        _emit_unit_table(),
        _emit_measurement_systems(),
        _emit_density_table(),
        _emit_gas_mark(),
        _emit_supported_price_units(),
    ]
    return "\n".join(parts)


def main() -> int:
    target = REPO_ROOT / "web_app" / "src" / "generated" / "units_table.ts"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(), encoding="utf-8")
    print(f"wrote {target.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
