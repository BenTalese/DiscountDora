from dataclasses import dataclass
from typing import List

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.recipe import Recipe


@dataclass
class Meal(BaseEntity):
    name: str
    recipes: List[Recipe]
