from dataclasses import dataclass
from typing import List

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.recipe import Recipe


@dataclass
class Meal(BaseEntity):
    NAME = "name"
    name: str

    QUANTITY_IN_STOCK = "quantity_in_stock"
    quantity_in_stock: int

    RECIPES = "recipes"
    recipes: List[Recipe]
