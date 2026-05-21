from dataclasses import dataclass
from typing import List

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.recipe import Recipe


@dataclass
class Meal(BaseEntity):
    name: str
    quantity_in_stock: int
    recipes: List[Recipe]

    class Fields(BaseEntity.Fields):
        NAME = "name"
        QUANTITY_IN_STOCK = "quantity_in_stock"
        RECIPES = "recipes"
