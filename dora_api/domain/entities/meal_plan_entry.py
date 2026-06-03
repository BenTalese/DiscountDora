from dataclasses import dataclass
from datetime import date, datetime

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.recipe import Recipe


@dataclass
class MealPlanEntry(BaseEntity):
    recipe: Recipe
    scheduled_for: date
    servings: int
    slot: str
    consumed_at: datetime | None = None

    class Fields(BaseEntity.Fields):
        RECIPE = "recipe"
        SCHEDULED_FOR = "scheduled_for"
        SERVINGS = "servings"
        SLOT = "slot"
        CONSUMED_AT = "consumed_at"
