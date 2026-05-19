from dataclasses import dataclass
from datetime import date

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.meal import Meal


@dataclass
class MealPlanEntry(BaseEntity):
    MEAL = "meal"
    meal: Meal

    SCHEDULED_FOR = "scheduled_for"
    scheduled_for: date

    SERVINGS = "servings"
    servings: int

    SLOT = "slot"
    slot: str
