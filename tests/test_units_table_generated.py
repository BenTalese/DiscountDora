"""Finalisation 20-R3 / 20-R4 (R-003) — the SPA's unit tables are generated,
not hand-maintained.

`web_app/src/generated/units_table.ts` is the single client-side copy of the
conversion table, measurement systems, price-display rules, and — since
20-R3/R4 — the DEC-3 no-space list and the countable-unit list that
`formatQuantity.ts` / `scaleQuantity.ts` read. This pins that the committed
file is exactly what `scripts/dump_units.py` renders from `units.py` today, so
a change to a server list that forgets to regenerate fails here instead of
drifting silently.

Regenerate with: python scripts/dump_units.py
"""
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED = REPO_ROOT / "web_app" / "src" / "generated" / "units_table.ts"


def _load_dump_units():
    spec = importlib.util.spec_from_file_location("dump_units", REPO_ROOT / "scripts" / "dump_units.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("dump_units", module)
    spec.loader.exec_module(module)
    return module


def test__units_table_generated_is_current():
    rendered = _load_dump_units().render()
    committed = GENERATED.read_text(encoding="utf-8")
    assert committed.replace("\r\n", "\n") == rendered.replace("\r\n", "\n"), (
        "web_app/src/generated/units_table.ts is stale — run `python scripts/dump_units.py`"
    )


def test__units_table__emits_the_two_word_lists():
    from dora_api.domain import units

    rendered = _load_dump_units().render()
    assert "export const NO_SPACE_UNITS" in rendered
    assert "export const COUNTABLE_UNITS" in rendered
    for word in units.NO_SPACE_UNITS | units.COUNTABLE_UNITS:
        assert f'"{word}"' in rendered, word
    # discrete sub-item parts are countable (cook-mode scaling rounds them);
    # the vague amounts stay continuous — "1.5 handfuls" is a fine quantity
    assert {"clove", "rasher", "slice", "sprig"} <= units.COUNTABLE_UNITS
    assert not ({"handful", "splash", "drizzle"} & units.COUNTABLE_UNITS)
