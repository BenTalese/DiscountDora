from typing import List
import uuid

from domain.entities.stock_item import StockItem


class Recipe:
    def __init__(
            self,
            id: uuid,
            image: bytes,
            ingredients: List[StockItem],
            instructions: str,
            name: str):
        self.id = id
        self.image = image
        self.ingredients = ingredients
        self.instructions = instructions
        self.name = name


# from typing import List, Optional

# class Ingredient:
#     def __init__(self, name: str, quantity: float, unit: str):
#         self.name = name
#         self.quantity = quantity
#         self.unit = unit

# class RecipeStep:
#     def __init__(self, description: str, ingredients: Optional[List[Ingredient]] = None,
#                  duration: Optional[int] = None, equipment: Optional[List[str]] = None):
#         self.description = description
#         self.ingredients = ingredients or []  # List of Ingredient instances
#         self.duration = duration  # Duration in minutes, for example
#         self.equipment = equipment or []  # List of equipment used

# class Recipe:
#     def __init__(self, name: str, steps: List[RecipeStep]):
#         self.name = name
#         self.steps = steps  # List of RecipeStep instances