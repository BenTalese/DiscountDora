"""How much does "2 leeks" or "1 cup of flour" weigh? — one answer, shared.

Extracted from `recipe_rollup` on 2026-09-09 (FU-905), when driving a realistic
recipe through both recipe calculators showed they were answering the same
question from different data and disagreeing about it:

* the **nutrition rollup** asked the linked food's `NutritionPortion` rows —
  measured values from the imported dataset ("1 cup flour = 125 g", "1 medium
  leek = 89 g", "1 clove = 3 g");
* **costing** had only `units.INGREDIENT_DENSITY_G_PER_ML`, a modelled table
  keyed on the ingredient's name, and no way to reach a portion row at all.

So a cup of plain flour was 125 g on the nutrition panel and 132.5 g in the
cost breakdown — 6% apart, on the same page — and "2 leeks" against a per-kilo
price was weighed correctly by one and reported unpriced by the other.

**Precedence, decided once, here: a measured portion beats a modelled
density.** A dataset row is somebody's scales; a density is an average
multiplied by an assumed cup. When both can answer, the row wins.

Nothing here guesses. Every path returns None rather than approximating, and
the callers report the gap in their own vocabulary (`no_conversion` for the
rollup, `unit_mismatch` for costing).

Portion rows are duck-typed on `.amount` / `.measure` / `.gram_weight` so the
pure half of this module needs no entity import and is directly testable with
plain objects.
"""
from typing import Iterable

from dora_api.domain import units
from dora_api.domain.entities.nutrition_portion import NutritionPortion
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.nutrition.text_matching import singular
from dora_api.infrastructure.ports import Repository
from dora_api.persistence.field import EntityField as Field


# USDA describes a whole item in one of these words; tried in order so
# "1 onion" lands on "medium" rather than the first row the dataset happens to
# hold. No match ⇒ unconvertible, never a guess.
COUNT_MEASURE_PREFERENCE = (
    "each", "whole", "medium", "fruit", "piece", "unit", "large", "small",
)


def measure_words(measure: str) -> set[str]:
    """USDA measures read like `cup, chopped` / `medium (2-1/2" dia)`. Split
    into comparable singular words so a plain "cup" matches the first."""
    cleaned = "".join(c if c.isalpha() else " " for c in (measure or "").lower())
    return {singular(word) for word in cleaned.split() if word}


def match_portion(portions: list, token: str):
    """The least-qualified portion whose measure mentions *token*.

    Least-qualified wins because "cup" in a recipe means a plain cup; a
    dataset row for `cup, chopped` weighs differently and is the wrong answer
    unless the recipe said chopped. Ties break on the measure text so the
    result never depends on row order.
    """
    wanted = singular(token)
    candidates = [
        portion for portion in portions
        if wanted in measure_words(portion.measure) and portion.gram_weight
        and portion.amount
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda portion: (len(portion.measure or ""), portion.measure or ""))
    return candidates[0]


def grams_from_portion(quantity: float, portion) -> float:
    return quantity / float(portion.amount) * float(portion.gram_weight)


def resolve_grams(
    quantity: float,
    unit: str | None,
    portions: list,
    names: Iterable[str],
) -> float | None:
    """Grams for *quantity* of *unit*, or None when it can't be known.

    `names` are the labels to try against the shared density table (the stock
    item's name, then the linked food's).
    """
    normalised = units.normalise_unit(unit or "")
    definition = units.find_unit(normalised) if normalised else None

    # A unit whose gram value belongs to one food ("stick" = butter) is only
    # ever answered by that food's own measured portion row — never by the
    # table's number, which would make two sticks of celery 226 g.
    food_specific = units.food_specific_mass(normalised)
    if food_specific is not None:
        for token in food_specific.portion_measures:
            portion = match_portion(portions, token)
            if portion is not None:
                return grams_from_portion(quantity, portion)
        return None

    if definition is not None and definition.dimension == units.MASS:
        return units.convert(quantity, normalised, "g")

    # A bare quantity ("2 eggs" with no unit) is a count.
    if not normalised or (definition is not None and definition.dimension == units.COUNT):
        for token in COUNT_MEASURE_PREFERENCE:
            portion = match_portion(portions, token)
            if portion is not None:
                return grams_from_portion(quantity, portion)
        return None

    if definition is not None and definition.dimension == units.VOLUME:
        # The measured portion beats the modelled density — the precedence
        # this module exists to state once.
        portion = match_portion(portions, definition.canonical.lower())
        if portion is None:
            portion = match_portion(portions, normalised)
        if portion is not None:
            return grams_from_portion(quantity, portion)
        for name in names:
            grams = units.convert(quantity, normalised, "g", ingredient=name)
            if grams is not None:
                return grams
        return None

    # Unknown unit word ("clove", "slice", "sprig") — only a portion row can
    # answer, and if none mentions it we say so rather than approximate.
    portion = match_portion(portions, normalised)
    return grams_from_portion(quantity, portion) if portion is not None else None


def food_ids_by_stock_item(repository: Repository, stock_item_ids: list) -> dict:
    """`stock_item_id → nutrition_food_id` for the whole batch, one query.

    Callers resolve the link this way rather than reading it off a loaded
    entity, so every path shares one code path (R-019). Only scalar columns are
    read, so there's no noload relationship to trip over (R-032).
    """
    if not stock_item_ids:
        return {}
    rows = repository.get(StockItem).where(
        Field(StockItem, "id").in_(stock_item_ids)
    ).all()
    return {
        row.id: row.nutrition_food_id
        for row in rows
        if row.nutrition_food_id is not None
    }


def portions_by_food(repository: Repository, food_ids: list) -> dict:
    """One query for the whole batch — the mapping carries no relationship
    object (R-032), so portions are gathered explicitly."""
    if not food_ids:
        return {}
    rows = repository.get(NutritionPortion).where(
        Field(NutritionPortion, NutritionPortion.Fields.NUTRITION_FOOD_ID).in_(food_ids)
    ).all()
    grouped: dict = {}
    for row in rows:
        grouped.setdefault(row.nutrition_food_id, []).append(row)
    return grouped


def portions_by_stock_item(repository: Repository, stock_item_ids: list) -> dict:
    """`stock_item_id → [portion rows]`, in two queries for the whole batch.

    The shape costing needs: it holds stock-item ids and doesn't otherwise care
    that a food sits between them and the weights.

    **Deliberately not gated on the nutrition mode.** These rows are present
    because a dataset was imported and foods were linked, and that is true
    whether or not nutrition is currently switched to complex. Gating would
    mean an install's grocery estimate silently got better when someone turned
    on a nutrition setting — a stranger coupling than reading data that is
    simply there. An install with no dataset gets `{}` and every caller falls
    back exactly as it did before (R-058 is about not *computing* money
    features when money is off, which the callers still honour).
    """
    if not stock_item_ids:
        return {}
    food_id_by_item = food_ids_by_stock_item(repository, stock_item_ids)
    if not food_id_by_item:
        return {}
    by_food = portions_by_food(repository, list(set(food_id_by_item.values())))
    return {
        item_id: by_food.get(food_id, [])
        for item_id, food_id in food_id_by_item.items()
    }
