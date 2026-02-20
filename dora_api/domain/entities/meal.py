from dataclasses import dataclass
from typing import List
from domain.entities.base_entity import BaseEntity

from domain.entities.recipe import Recipe


@dataclass(slots=True)
class Meal(BaseEntity):
    name: str
    recipes: List[Recipe]
