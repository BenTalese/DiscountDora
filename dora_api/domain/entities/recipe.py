from dataclasses import dataclass
from datetime import datetime
from typing import List

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient


@dataclass
class Recipe(BaseEntity):
    CATEGORY = "category"
    category: str | None

    COOK_TIME_MINUTES = "cook_time_minutes"
    cook_time_minutes: int | None

    CUISINE = "cuisine"
    cuisine: str | None

    DIFFICULTY = "difficulty"
    difficulty: str | None

    IMAGE = "image"
    image: bytes | None

    INGREDIENTS = "ingredients"
    ingredients: List[RecipeIngredient]

    INSTRUCTIONS = "instructions"
    instructions: str | None

    IS_FAVOURITE = "is_favourite"
    is_favourite: bool

    LAST_MADE_ON = "last_made_on"
    last_made_on: datetime | None

    NAME = "name"
    name: str

    NUTRITION = "nutrition"
    nutrition: str | None

    PREP_TIME_MINUTES = "prep_time_minutes"
    prep_time_minutes: int | None

    RECIPE_COLLECTION = "recipe_collection"
    recipe_collection: RecipeCollection | None

    SERVINGS = "servings"
    servings: int | None

    TIME_OF_DAY = "time_of_day"
    time_of_day: str | None
