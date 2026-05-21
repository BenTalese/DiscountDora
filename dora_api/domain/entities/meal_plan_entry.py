from dataclasses import dataclass
from datetime import date

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.meal import Meal


@dataclass
class MealPlanEntry(BaseEntity):
    meal: Meal
    scheduled_for: date
    servings: int
    slot: str

    class Fields(BaseEntity.Fields):
        MEAL = "meal"
        SCHEDULED_FOR = "scheduled_for"
        SERVINGS = "servings"
        SLOT = "slot"
