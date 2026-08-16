"""Recipe nutrition rollup — gram conversion, coverage honesty, and the
per-serving basis.

The numbers here are the whole point of complex mode, so what's pinned is
mostly *when we refuse to answer*: an ingredient whose weight can't be known
must land in the coverage line rather than be approximated, because a total
that quietly skips two ingredients while presenting itself as complete is
worse than no total at all.
"""
from uuid import uuid4

import pytest

from dora_api.features.nutrition.recipe_rollup import (
    BASIS_RECIPE,
    BASIS_SERVING,
    RecipeNutrition,
    effective_kcal_per_serving,
    REASON_NOT_LINKED,
    REASON_NO_CONVERSION,
    REASON_NO_DATA,
    REASON_NO_FOOD,
    REASON_NO_QUANTITY,
    rollup_recipe_nutrition,
)


class _Food:
    def __init__(self, name, kcal=100.0, protein=None, carbs=None, fat=None):
        self.id = uuid4()
        self.name = name
        self.kcal_per_100g = kcal
        self.protein_g_per_100g = protein
        self.carbs_g_per_100g = carbs
        self.fat_g_per_100g = fat


class _Portion:
    def __init__(self, food_id, amount, measure, gram_weight):
        self.nutrition_food_id = food_id
        self.amount = amount
        self.measure = measure
        self.gram_weight = gram_weight


class _StockItem:
    def __init__(self, name, food=None):
        self.id = uuid4()
        self.name = name
        self.nutrition_food_id = food.id if food else None


class _Ingredient:
    def __init__(self, stock_item=None, quantity=None, unit=None, is_optional=False):
        self.stock_item = stock_item
        self.quantity = quantity
        self.unit = unit
        self.is_optional = is_optional


class _Recipe:
    def __init__(self, ingredients, servings=None):
        self.id = uuid4()
        self.ingredients = ingredients
        self.servings = servings


class _Repo:
    """Serves the three batch queries the rollup makes, without a database.

    Deliberately ignores the filter condition and returns everything seeded —
    the repository query path itself is covered by the e2e suite; here the
    subject is the arithmetic. Stock items are collected from the recipe under
    test so the `stock_item → food` hop resolves the same way it does live.
    """
    def __init__(self, foods=(), portions=(), stock_items=()):
        self._foods = list(foods)
        self._portions = list(portions)
        self._stock_items = list(stock_items)
        self._pending = None

    def get(self, entity):
        self._pending = entity.__name__
        return self

    def where(self, _condition):
        return self

    def all(self):
        if self._pending == "StockItem":
            return self._stock_items
        if self._pending == "NutritionFood":
            return self._foods
        return self._portions


def _repo_for(recipe, foods=(), portions=()):
    """A repo double seeded with the recipe's own stock items."""
    items = [
        ing.stock_item for ing in recipe.ingredients if ing.stock_item is not None
    ]
    return _Repo(foods=foods, portions=portions, stock_items=items)


#region gram conversion

def test__rollup__MassUnit__ConvertsDirectly():
    food = _Food("Flour", kcal=364.0)
    recipe = _Recipe([_Ingredient(_StockItem("Flour", food), 250, "g")], servings=1)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food]), recipe)

    assert result.kcal == pytest.approx(910)
    assert (result.counted_count, result.total_count) == (1, 1)


def test__rollup__KilogramsAndOunces__NormaliseToGrams():
    food = _Food("Rice", kcal=130.0)
    recipe = _Recipe(
        [
            _Ingredient(_StockItem("Rice", food), 0.5, "kg"),
            _Ingredient(_StockItem("Rice", food), 1, "oz"),
        ],
        servings=1,
    )

    result = rollup_recipe_nutrition(_repo_for(recipe, [food]), recipe)

    # 500g + 28.3495g at 130 kcal/100g.
    assert result.kcal == pytest.approx(round((500 + 28.3495) / 100 * 130))


def test__rollup__VolumeWithMatchingPortion__PrefersTheMeasuredPortionOverDensity():
    # "cup" is in the density table as flour (0.53 g/ml → 132.5g per AU cup),
    # but the food's own portion row says 125g. The measured row wins.
    food = _Food("Flour", kcal=100.0)
    portion = _Portion(food.id, 1, "cup", 125.0)
    recipe = _Recipe([_Ingredient(_StockItem("flour", food), 2, "cups")], servings=1)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food], [portion]), recipe)

    assert result.kcal == pytest.approx(250)


def test__rollup__VolumeWithoutPortion__FallsBackToTheSharedDensityTable():
    food = _Food("Milk", kcal=100.0)
    recipe = _Recipe([_Ingredient(_StockItem("milk", food), 500, "ml")], servings=1)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food]), recipe)

    # milk density 1.03 g/ml → 515g.
    assert result.kcal == pytest.approx(515)


def test__rollup__PortionMatching__TakesTheLeastQualifiedMeasure():
    # A recipe saying "1 cup" means a plain cup; "cup, chopped" weighs
    # differently and is the wrong answer unless the recipe said chopped.
    food = _Food("Onion", kcal=100.0)
    portions = [
        _Portion(food.id, 1, "cup, chopped", 160.0),
        _Portion(food.id, 1, "cup", 110.0),
    ]
    recipe = _Recipe([_Ingredient(_StockItem("onion", food), 1, "cup")], servings=1)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food], portions), recipe)

    assert result.kcal == pytest.approx(110)


def test__rollup__CountWithNoUnit__UsesAWholeItemPortion():
    food = _Food("Bananas, raw", kcal=89.0)
    portions = [
        _Portion(food.id, 1, "cup, sliced", 150.0),
        _Portion(food.id, 1, "medium (7\" long)", 118.0),
    ]
    recipe = _Recipe([_Ingredient(_StockItem("Banana", food), 2, None)], servings=1)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food], portions), recipe)

    assert result.kcal == pytest.approx(round(2 * 118 / 100 * 89))


def test__rollup__CountWithNoWholeItemPortion__IsUnconvertibleNotGuessed():
    food = _Food("Onion", kcal=40.0)
    portions = [_Portion(food.id, 1, "cup, chopped", 160.0)]
    recipe = _Recipe([_Ingredient(_StockItem("Onion", food), 1, None)], servings=1)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food], portions), recipe)

    assert result.kcal is None
    assert result.uncounted == {REASON_NO_CONVERSION: 1}


def test__rollup__UnknownUnitWord__AnsweredOnlyByAPortionRow():
    food = _Food("Garlic", kcal=149.0)
    portions = [_Portion(food.id, 1, "clove", 3.0)]
    recipe = _Recipe([_Ingredient(_StockItem("Garlic", food), 3, "cloves")], servings=1)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food], portions), recipe)

    assert result.kcal == pytest.approx(round(9 / 100 * 149))


def test__rollup__UnknownUnitWordWithNoPortion__IsUnconvertible():
    food = _Food("Parsley", kcal=36.0)
    recipe = _Recipe([_Ingredient(_StockItem("Parsley", food), 2, "sprigs")], servings=1)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food]), recipe)

    assert result.uncounted == {REASON_NO_CONVERSION: 1}

#endregion

#region coverage honesty

def test__rollup__EveryFailureKind__IsNamedInTheCoverageMap():
    good = _Food("Flour", kcal=364.0)
    dataless = _Food("Water", kcal=None)
    recipe = _Recipe(
        [
            _Ingredient(_StockItem("Flour", good), 100, "g"),
            _Ingredient(None, 1, "g"),                                   # not linked
            _Ingredient(_StockItem("Salt"), 1, "g"),                     # no food
            _Ingredient(_StockItem("Water", dataless), 1, "g"),          # no kcal
            _Ingredient(_StockItem("Pepper", good), None, None),         # no quantity
            _Ingredient(_StockItem("Basil", good), 2, "sprigs"),         # no conversion
        ],
        servings=1,
    )

    result = rollup_recipe_nutrition(_repo_for(recipe, [good, dataless]), recipe)

    assert (result.counted_count, result.total_count) == (1, 6)
    assert result.uncounted == {
        REASON_NOT_LINKED: 1,
        REASON_NO_FOOD: 1,
        REASON_NO_DATA: 1,
        REASON_NO_QUANTITY: 1,
        REASON_NO_CONVERSION: 1,
    }


def test__rollup__NothingCountable__ReportsNullsRatherThanZero():
    recipe = _Recipe([_Ingredient(None, 1, "g"), _Ingredient(None, 2, "g")])

    result = rollup_recipe_nutrition(_repo_for(recipe), recipe)

    assert (result.kcal, result.protein_g, result.carbs_g, result.fat_g) == (None, None, None, None)
    assert (result.counted_count, result.total_count) == (0, 2)


def test__rollup__MacroMissingOnEveryCountedFood__StaysNullWhileKcalCounts():
    # A source can know kcal but not fat; a 0 would read as "this recipe has
    # no fat", which is a different claim from "nobody told us".
    food = _Food("Flour", kcal=364.0, protein=10.3)
    recipe = _Recipe([_Ingredient(_StockItem("Flour", food), 100, "g")], servings=1)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food]), recipe)

    assert result.kcal == pytest.approx(364)
    assert result.protein_g == pytest.approx(10.3)
    assert result.fat_g is None


def test__rollup__OptionalIngredients__SitOutsideBothHalvesOfTheRatio():
    food = _Food("Flour", kcal=364.0)
    recipe = _Recipe(
        [
            _Ingredient(_StockItem("Flour", food), 100, "g"),
            _Ingredient(_StockItem("Truffle", food), 100, "g", is_optional=True),
        ],
        servings=1,
    )

    result = rollup_recipe_nutrition(_repo_for(recipe, [food]), recipe)

    assert (result.counted_count, result.total_count) == (1, 1)
    assert result.kcal == pytest.approx(364)

#endregion

#region basis

def test__rollup__ServingsTypedIn__DividesPerServing():
    food = _Food("Flour", kcal=100.0, protein=10.0)
    recipe = _Recipe([_Ingredient(_StockItem("Flour", food), 400, "g")], servings=4)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food]), recipe)

    assert result.basis == BASIS_SERVING
    assert result.servings == 4
    assert result.kcal == pytest.approx(100)
    assert result.protein_g == pytest.approx(10.0)


@pytest.mark.parametrize("servings", [None, 0])
def test__rollup__NoServings__ReportsTheWholeRecipeAndSaysSo(servings):
    food = _Food("Flour", kcal=100.0)
    recipe = _Recipe([_Ingredient(_StockItem("Flour", food), 400, "g")], servings=servings)

    result = rollup_recipe_nutrition(_repo_for(recipe, [food]), recipe)

    assert result.basis == BASIS_RECIPE
    assert result.servings is None
    assert result.kcal == pytest.approx(400)

#endregion


#region effective per-serving figure (what every surface reads)

def _rollup(**over) -> RecipeNutrition:
    base = dict(
        basis=BASIS_SERVING, servings=4, kcal=500.0, protein_g=None, carbs_g=None,
        fat_g=None, counted_count=8, total_count=8, uncounted={}, is_reliable=True,
    )
    base.update(over)
    return RecipeNutrition(**base)


def test__effective_kcal__SimpleMode__UsesTheTypedNumberAndTrustsIt():
    # No coverage to doubt — the user asserted it themselves.
    assert effective_kcal_per_serving("simple", 420, None) == (420.0, True)


def test__effective_kcal__SimpleModeWithNothingTyped__HasNoFigure():
    assert effective_kcal_per_serving("simple", None, None) == (None, False)


def test__effective_kcal__ComplexMode__UsesTheRollupAndIgnoresAStaleTypedNumber():
    assert effective_kcal_per_serving("complex", 999, _rollup(kcal=500.0)) == (500.0, True)


def test__effective_kcal__ComplexModeThinCoverage__ShowsTheFigureButWontBeJudgedOn():
    assert effective_kcal_per_serving(
        "complex", None, _rollup(kcal=500.0, counted_count=1, is_reliable=False),
    ) == (500.0, False)


def test__effective_kcal__WholeRecipeBasis__RefusesToInventAPerServingFigure():
    # No servings typed in, so the rollup's number is the whole pot. Dividing
    # it by a serving count nobody stated would invent the answer.
    assert effective_kcal_per_serving(
        "complex", None, _rollup(basis=BASIS_RECIPE, servings=None),
    ) == (None, False)


def test__effective_kcal__NutritionOff__SaysNothingEvenWithDataAvailable():
    assert effective_kcal_per_serving("off", 420, _rollup()) == (None, False)

#endregion
