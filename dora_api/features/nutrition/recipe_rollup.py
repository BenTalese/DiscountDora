"""Server-owned recipe nutrition rollup (FU-635 chunk 6).

Complex mode's one user-facing number: what a serving of this recipe holds,
summed from the foods its ingredients are linked to. Sibling of
`features/recipes/recipe_cost.py` — same shape (server owns the math, R-003;
the client renders it and never re-derives it), same honesty contract (a
partial total is always shown *with* its coverage, never as a clean figure).

The chain per ingredient is:

    RecipeIngredient.quantity + unit
      → StockItem.nutrition_food_id
        → NutritionFood (nutrients per 100g)
        + NutritionPortion (a household measure → its gram weight)
      → grams → nutrients

Every link can fail, and each failure is *named* rather than swallowed —
`uncounted` carries a count per reason so the UI can say "3 ingredients
aren't linked to a food" instead of an unexplained shortfall (P3 Honest).

**Grams are never guessed.** Mass units convert outright; volumes prefer the
food's own USDA portion row ("1 cup, chopped" → 125 g) and fall back to the
shared density table only when the food has no matching portion; counts
("2 bananas") need a portion row and are reported unconvertible without one.
Nothing here invents a weight (P12 No-invent) — an unconvertible ingredient
lands in the coverage line, where a partial total can't pass for a complete
one.

Optional ingredients sit outside both halves of the coverage ratio, matching
the cookability rule's treatment of them (R-003): they aren't part of the
recipe as written, so they neither add nutrients nor count as a gap.
"""
from dataclasses import dataclass
from typing import Iterable, List

from dora_api.domain import units
from dora_api.domain.entities.nutrition_food import NutritionFood
from dora_api.domain.entities.nutrition_portion import NutritionPortion
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.nutrition.text_matching import singular
from dora_api.infrastructure.ports import Repository
from dora_api.persistence.field import EntityField as Field


# Why an ingredient contributed nothing. Closed set (R-010) — the SPA maps
# each to its own copy line, so a new reason can never arrive unlabelled.
REASON_NOT_LINKED = "not_linked"        # no stock item on the ingredient row
REASON_NO_FOOD = "no_food"              # stock item isn't linked to a food
REASON_NO_QUANTITY = "no_quantity"      # "salt to taste" — nothing to weigh
REASON_NO_CONVERSION = "no_conversion"  # quantity known, grams unknowable
REASON_NO_DATA = "no_data"              # food carries no kcal figure
UNCOUNTED_REASONS = (
    REASON_NOT_LINKED,
    REASON_NO_FOOD,
    REASON_NO_QUANTITY,
    REASON_NO_CONVERSION,
    REASON_NO_DATA,
)

# What the figure is per. `servings` is user-typed and often unset; rather
# than divide by a guessed 4 we report the whole-recipe total and say so.
BASIS_SERVING = "serving"
BASIS_RECIPE = "recipe"

# Count-unit portion matching. USDA describes a whole item in one of these
# words; tried in order so "1 onion" lands on "medium" rather than the first
# row the dataset happens to hold. No match ⇒ unconvertible, never a guess.
_COUNT_MEASURE_PREFERENCE = (
    "each", "whole", "medium", "fruit", "piece", "unit", "large", "small",
)


# Coverage at or above which the estimate is solid enough to *judge* a recipe
# on — filter it out of a "≤ N kcal" search, or rank it against its peers.
# Displaying a partial figure with its coverage is always fine; excluding a
# recipe from a search on the strength of a 3-of-12 estimate is not, and for
# someone eating to a number that's worse than showing nothing (R-041).
# Threshold lives here alone — the client reads the resulting boolean and never
# re-derives it (R-003).
RELIABLE_COVERAGE_RATIO = 0.8


@dataclass(frozen=True, slots=True)
class IngredientInput:
    """The only ingredient facts the rollup needs. Both callers flatten to this
    — the detail path from loaded entities, the list path from its DTOs — so
    there is one arithmetic path rather than two that drift."""
    stock_item_id: object | None
    stock_item_name: str | None
    quantity: float | None
    unit: str | None
    is_optional: bool = False


@dataclass(frozen=True, slots=True)
class RecipeNutritionInput:
    recipe_id: object
    servings: int | None
    ingredients: List[IngredientInput]


def input_from_entity(recipe) -> RecipeNutritionInput:  # noqa: ANN001
    """Adapter for the detail path — a loaded `Recipe` with its ingredients'
    `stock_item` included."""
    return RecipeNutritionInput(
        recipe_id = recipe.id,
        servings = recipe.servings,
        ingredients = [
            IngredientInput(
                stock_item_id = ing.stock_item.id if ing.stock_item else None,
                stock_item_name = ing.stock_item.name if ing.stock_item else None,
                quantity = ing.quantity,
                unit = ing.unit,
                is_optional = getattr(ing, "is_optional", False),
            )
            for ing in (recipe.ingredients or [])
        ],
    )


@dataclass(frozen=True, slots=True)
class RecipeNutrition:
    """Per-recipe result. Nutrient fields are None when *no* counted
    ingredient carried that nutrient — a source can know kcal but not fibre,
    and a 0 would read as "this recipe has no fat"."""
    basis: str
    servings: int | None
    kcal: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    counted_count: int
    total_count: int
    uncounted: dict[str, int]
    # Whether the estimate covers enough of the recipe to rank or filter on
    # (see RELIABLE_COVERAGE_RATIO). Display is never gated on this — a partial
    # figure shown with its coverage is honest; a partial figure used to hide a
    # recipe from a calorie search is not.
    is_reliable: bool = False


def _measure_words(measure: str) -> set[str]:
    """USDA measures read like `cup, chopped` / `medium (2-1/2" dia)`. Split
    into comparable singular words so a plain "cup" matches the first."""
    cleaned = "".join(c if c.isalpha() else " " for c in (measure or "").lower())
    return {singular(word) for word in cleaned.split() if word}


def _match_portion(portions: list, token: str):
    """The least-qualified portion whose measure mentions *token*.

    Least-qualified wins because "cup" in a recipe means a plain cup; a
    dataset row for `cup, chopped` weighs differently and is the wrong answer
    unless the recipe said chopped. Ties break on the measure text so the
    result never depends on row order.
    """
    wanted = singular(token)
    candidates = [
        portion for portion in portions
        if wanted in _measure_words(portion.measure) and portion.gram_weight
        and portion.amount
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda portion: (len(portion.measure or ""), portion.measure or ""))
    return candidates[0]


def _grams_from_portion(quantity: float, portion) -> float:
    return quantity / float(portion.amount) * float(portion.gram_weight)


def _resolve_grams(quantity: float, unit: str | None, portions: list, names: Iterable[str]) -> float | None:
    """Grams for *quantity* of *unit*, or None when it can't be known.

    `names` are the labels to try against the shared density table (the stock
    item's name, then the linked food's) — density is the last resort for a
    volume, since the food's own portion row is measured, not modelled.
    """
    normalised = units.normalise_unit(unit or "")
    definition = units.find_unit(normalised) if normalised else None

    if definition is not None and definition.dimension == units.MASS:
        return units.convert(quantity, normalised, "g")

    # A bare quantity ("2 eggs" with no unit) is a count.
    if not normalised or (definition is not None and definition.dimension == units.COUNT):
        for token in _COUNT_MEASURE_PREFERENCE:
            portion = _match_portion(portions, token)
            if portion is not None:
                return _grams_from_portion(quantity, portion)
        return None

    if definition is not None and definition.dimension == units.VOLUME:
        # The food's own measured portion beats a modelled density.
        portion = _match_portion(portions, definition.canonical.lower())
        if portion is None:
            portion = _match_portion(portions, normalised)
        if portion is not None:
            return _grams_from_portion(quantity, portion)
        for name in names:
            grams = units.convert(quantity, normalised, "g", ingredient=name)
            if grams is not None:
                return grams
        return None

    # Unknown unit word ("clove", "slice", "sprig") — only a portion row can
    # answer, and if none mentions it we say so rather than approximate.
    portion = _match_portion(portions, normalised)
    return _grams_from_portion(quantity, portion) if portion is not None else None


def _food_ids_by_stock_item(repository: Repository, stock_item_ids: list) -> dict:
    """`stock_item_id → nutrition_food_id` for the whole batch, one query.

    Both callers resolve the link this way rather than reading it off a loaded
    entity, so the list and detail paths share one code path (R-019). Only
    scalar columns are read, so there's no noload relationship to trip over
    (R-032).
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


def _foods_by_id(repository: Repository, food_ids: list) -> dict:
    if not food_ids:
        return {}
    rows = repository.get(NutritionFood).where(
        Field(NutritionFood, "id").in_(food_ids)
    ).all()
    return {row.id: row for row in rows}


def _portions_by_food(repository: Repository, food_ids: list) -> dict:
    """One query for the whole recipe — the mapping carries no relationship
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


def _rollup_one(recipe: 'RecipeNutritionInput', food_ids_by_item: dict, foods: dict, portions: dict) -> RecipeNutrition:
    totals = {"kcal": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    contributors = dict.fromkeys(totals, 0)
    uncounted = {reason: 0 for reason in UNCOUNTED_REASONS}
    counted = 0

    required = [ing for ing in recipe.ingredients if not ing.is_optional]
    for ingredient in required:
        if ingredient.stock_item_id is None:
            uncounted[REASON_NOT_LINKED] += 1
            continue
        food_id = food_ids_by_item.get(ingredient.stock_item_id)
        food = foods.get(food_id) if food_id else None
        if food is None:
            uncounted[REASON_NO_FOOD] += 1
            continue
        if food.kcal_per_100g is None:
            # kcal is the load-bearing figure; a food without one can't
            # contribute to the headline, so it reads as a gap either way.
            uncounted[REASON_NO_DATA] += 1
            continue
        quantity = ingredient.quantity
        if quantity is None or quantity <= 0:
            uncounted[REASON_NO_QUANTITY] += 1
            continue
        grams = _resolve_grams(
            float(quantity),
            ingredient.unit,
            portions.get(food.id, []),
            [name for name in (ingredient.stock_item_name, food.name) if name],
        )
        if grams is None:
            uncounted[REASON_NO_CONVERSION] += 1
            continue

        counted += 1
        hundreds = grams / 100.0
        for key, per_100g in (
            ("kcal", food.kcal_per_100g),
            ("protein_g", food.protein_g_per_100g),
            ("carbs_g", food.carbs_g_per_100g),
            ("fat_g", food.fat_g_per_100g),
        ):
            if per_100g is None:
                continue
            totals[key] += hundreds * float(per_100g)
            contributors[key] += 1

    servings = recipe.servings if (recipe.servings or 0) > 0 else None
    divisor = float(servings) if servings else 1.0
    total_count = len(required)

    def per_basis(key: str, places: int) -> float | None:
        if contributors[key] == 0:
            return None
        return round(totals[key] / divisor, places)

    return RecipeNutrition(
        basis = BASIS_SERVING if servings else BASIS_RECIPE,
        servings = servings,
        kcal = per_basis("kcal", 0),
        protein_g = per_basis("protein_g", 1),
        carbs_g = per_basis("carbs_g", 1),
        fat_g = per_basis("fat_g", 1),
        counted_count = counted,
        total_count = total_count,
        uncounted = {reason: count for reason, count in uncounted.items() if count},
        is_reliable = (
            counted > 0 and total_count > 0
            and (counted / total_count) >= RELIABLE_COVERAGE_RATIO
        ),
    )


def effective_kcal_per_serving(mode: str, typed_kcal, rollup: RecipeNutrition | None) -> tuple:
    """The one answer to "what does a serving of this recipe cost, calorie-wise?"

    Which field holds it depends on the mode — `simple` uses the number the
    user typed, `complex` the rollup over linked foods — and three surfaces now
    ask (cookbook card, kcal filter/sort, meal-plan entries). Deciding it once
    here, server-side, is R-003: the alternative was each client re-deriving
    "which field, and may I trust it", which is precisely how two surfaces end
    up disagreeing about the same recipe.

    Returns `(kcal_per_serving, is_reliable)`. `is_reliable` says whether the
    figure may be used to *judge* the recipe (filter it out, rank it) as
    opposed to merely display it (R-041).

    A complex rollup whose basis is the *whole recipe* — no servings typed in —
    deliberately yields None: dividing it by a serving count nobody stated
    would invent the very number being asked for (P12).
    """
    from dora_api.domain.entities.app_setting import (
        NUTRITION_MODE_COMPLEX, NUTRITION_MODE_SIMPLE,
    )

    if mode == NUTRITION_MODE_SIMPLE:
        # A hand-typed figure carries no coverage to doubt — the user asserted
        # it, so it's as judgeable as it is accurate.
        return (float(typed_kcal), True) if typed_kcal is not None else (None, False)
    if mode == NUTRITION_MODE_COMPLEX and rollup is not None:
        if rollup.kcal is None or rollup.basis != BASIS_SERVING:
            return (None, False)
        return (rollup.kcal, rollup.is_reliable)
    return (None, False)


def rollup_recipes_nutrition(repository: Repository, recipes: Iterable['RecipeNutritionInput']) -> dict:
    """`recipe_id → RecipeNutrition` for every recipe passed. Three queries
    total (stock-item links, foods, portions) regardless of how many recipes —
    the cookbook list calls this for a whole page."""
    recipes = list(recipes)
    stock_item_ids = list({
        ingredient.stock_item_id
        for recipe in recipes
        for ingredient in recipe.ingredients
        if ingredient.stock_item_id is not None and not ingredient.is_optional
    })
    food_ids_by_item = _food_ids_by_stock_item(repository, stock_item_ids)
    food_ids = list(set(food_ids_by_item.values()))
    foods = _foods_by_id(repository, food_ids)
    portions = _portions_by_food(repository, food_ids)
    return {
        recipe.recipe_id: _rollup_one(recipe, food_ids_by_item, foods, portions)
        for recipe in recipes
    }


def rollup_recipe_nutrition(repository: Repository, recipe) -> RecipeNutrition:  # noqa: ANN001
    """Single-recipe path (the detail endpoint). `recipe` is the loaded entity;
    its `ingredients[].stock_item` must be included, which the recipe-detail
    query already does."""
    single = input_from_entity(recipe)
    return rollup_recipes_nutrition(repository, [single])[single.recipe_id]
