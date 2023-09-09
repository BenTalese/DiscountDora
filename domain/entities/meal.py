from typing import List
import uuid

from domain.entities.recipe import Recipe


class Meal:
    def __init__(
            self,
            id: uuid,
            name: str,
            recipes: List[Recipe]):
        self.id = id
        self.name = name
        self.recipes = recipes