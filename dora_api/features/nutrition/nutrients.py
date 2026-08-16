"""The nutrient set Dora stores, and how each source names it.

One module so adding a nutrient is a single edit. Before this existed the
mapping lived in three places — the bulk CSV importer's `_WANTED_NUTRIENTS`,
the live USDA-API parser's if/elif chain, and the Open Food Facts parser's
field list — which is exactly the drift R-002 exists to stop: a nutrient added
to the importer but not to the API path would silently be blank for installs
that use the live key.

Scope (owner decision 2026-08-16): energy + the macros a shopper actually reads
off a pack. Deliberately NOT the full USDA nutrient table (vitamins, minerals,
amino acids) — those need a per-nutrient child table, and every source is
sparse enough that the UI would be mostly blank rows. `kcal_per_100g` stays the
only value the app treats as load-bearing; everything else is display-only, and
NULL means "this source didn't say", never zero (P12 No-invent).
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True, slots=True)
class Nutrient:
    """One stored nutrient and everything needed to read or render it."""
    attr: str
    label: str
    unit: str
    # USDA `(nutrient name, unit)` pairs, lowercased. More than one because
    # Foundation and SR Legacy disagree on the sugar row's name.
    usda_keys: Tuple[Tuple[str, str], ...]
    # Open Food Facts `nutriments` key, when OFF carries the value.
    off_key: Optional[str] = None
    # Multiplier applied to the OFF value to reach our stored unit. OFF reports
    # sodium in GRAMS per 100g while we store milligrams, and getting that
    # wrong is a 1000× error on a number people actually watch.
    off_scale: float = 1.0


# Display order too — the UI renders the list in this sequence.
NUTRIENTS: Tuple[Nutrient, ...] = (
    Nutrient(
        attr="kcal_per_100g", label="Energy", unit="kcal",
        usda_keys=(("energy", "kcal"),),
        off_key="energy-kcal_100g",
    ),
    Nutrient(
        attr="protein_g_per_100g", label="Protein", unit="g",
        usda_keys=(("protein", "g"),),
        off_key="proteins_100g",
    ),
    Nutrient(
        attr="carbs_g_per_100g", label="Carbohydrate", unit="g",
        usda_keys=(("carbohydrate, by difference", "g"),),
        off_key="carbohydrates_100g",
    ),
    Nutrient(
        attr="sugars_g_per_100g", label="Sugars", unit="g",
        usda_keys=(
            ("total sugars", "g"),
            ("sugars, total including nlea", "g"),
            ("sugars, total", "g"),
        ),
        off_key="sugars_100g",
    ),
    Nutrient(
        attr="fat_g_per_100g", label="Fat", unit="g",
        usda_keys=(("total lipid (fat)", "g"),),
        off_key="fat_100g",
    ),
    Nutrient(
        attr="saturated_fat_g_per_100g", label="Saturated fat", unit="g",
        usda_keys=(("fatty acids, total saturated", "g"),),
        off_key="saturated-fat_100g",
    ),
    Nutrient(
        attr="fibre_g_per_100g", label="Fibre", unit="g",
        usda_keys=(("fiber, total dietary", "g"),),
        off_key="fiber_100g",
    ),
    Nutrient(
        attr="sodium_mg_per_100g", label="Sodium", unit="mg",
        usda_keys=(("sodium, na", "mg"),),
        off_key="sodium_100g", off_scale=1000.0,
    ),
)

NUTRIENT_ATTRS: Tuple[str, ...] = tuple(n.attr for n in NUTRIENTS)

# (lowercased USDA nutrient name, lowercased unit) → attribute name.
USDA_NUTRIENT_ATTRS: Dict[Tuple[str, str], str] = {
    key: nutrient.attr
    for nutrient in NUTRIENTS
    for key in nutrient.usda_keys
}


def off_values(nutriments: dict, to_float) -> Dict[str, float]:  # noqa: ANN001
    """Pull our nutrient set out of an OFF `nutriments` blob.

    `to_float` is injected rather than imported so this module stays free of
    the lookup module's parsing helpers (and the import cycle that would come
    with it). Missing keys are omitted, not zeroed.
    """
    values: Dict[str, float] = {}
    for nutrient in NUTRIENTS:
        if not nutrient.off_key:
            continue
        amount = to_float(nutriments.get(nutrient.off_key))
        if amount is not None:
            values[nutrient.attr] = amount * nutrient.off_scale
    return values
