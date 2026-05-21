from dataclasses import dataclass
from datetime import datetime
from typing import List

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient


@dataclass
class Recipe(BaseEntity):
    category: str | None
    cook_time_minutes: int | None
    cuisine: str | None
    difficulty: str | None
    image: bytes | None
    ingredients: List[RecipeIngredient]
    instructions: str | None
    is_favourite: bool
    last_made_on: datetime | None
    name: str
    nutrition: str | None
    prep_time_minutes: int | None
    recipe_collection: RecipeCollection | None
    servings: int | None
    time_of_day: str | None

    class Fields(BaseEntity.Fields):
        CATEGORY = "category"
        COOK_TIME_MINUTES = "cook_time_minutes"
        CUISINE = "cuisine"
        DIFFICULTY = "difficulty"
        IMAGE = "image"
        INGREDIENTS = "ingredients"
        INSTRUCTIONS = "instructions"
        IS_FAVOURITE = "is_favourite"
        LAST_MADE_ON = "last_made_on"
        NAME = "name"
        NUTRITION = "nutrition"
        PREP_TIME_MINUTES = "prep_time_minutes"
        RECIPE_COLLECTION = "recipe_collection"
        SERVINGS = "servings"
        TIME_OF_DAY = "time_of_day"
