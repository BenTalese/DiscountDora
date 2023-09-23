from dataclasses import dataclass
from typing import List
import uuid

from domain.entities.recipe import Recipe


@dataclass
class Meal:
    id: uuid = None
    name: str = None
    recipes: List[Recipe] = None
