"""Nutrition complex-mode — a household measure and what it weighs.

This is the table that makes recipe rollup possible at all. Nutrient values
are stored per 100g, but recipes say "2 cups flour" or "1 onion", so every
rollup needs a gram weight for the quantity actually written down.

USDA's FoodData Central ships exactly this (`food_portion.csv`): per food,
rows like `1 · "cup, chopped" · 125g` or `1 · "medium" · 118g`. Importing it
alongside the foods is what turns "2 bananas" into grams without asking the
user to weigh anything.

Where a food has no matching portion row, the ingredient is reported as
**not convertible** rather than guessed at — it shows up in the recipe's
coverage line so a partial total can never pass itself off as complete.
"""
from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class NutritionPortion(BaseEntity):
    nutrition_food_id: UUID
    # The measure as the source states it: amount + description. "1" +
    # "cup, chopped"; "1" + "medium"; "2" + "tbsp". Kept as the source's own
    # wording rather than normalised into the app's unit vocabulary — the
    # matcher reads it, and a human picking a portion should see what the
    # source actually said.
    amount: float
    measure: str
    gram_weight: float

    class Fields(BaseEntity.Fields):
        NUTRITION_FOOD_ID = "nutrition_food_id"
        AMOUNT = "amount"
        MEASURE = "measure"
        GRAM_WEIGHT = "gram_weight"
