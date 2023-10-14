from dataclasses import dataclass
from typing import List
from domain.entities.base_entity import BaseEntity

from domain.entities.recipe import Recipe


@dataclass
class Meal(BaseEntity):
    name: str = None
    recipes: List[Recipe] = None
