from typing import List
import uuid

from domain.entities.recipe import Recipe


class Meal:
    id: uuid
    name: str
    recipes: List[Recipe]
