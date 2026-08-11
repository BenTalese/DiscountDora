from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.recipe import Recipe


@dataclass
class MealPlanEntry(BaseEntity):
    recipe: Recipe
    scheduled_for: date
    servings: int
    slot: str
    consumed_at: datetime | None = None
    # PROPOSAL_MEAL_PLANS_PART_2 — when set, this meal is one slot of a shared
    # `CookBatch` (cook once, eat across several days). Plain FK id (SET NULL on
    # batch delete), not a relationship — grouping reads it directly. NULL = a
    # standalone meal (the pre-Part-2 default). The batch's cook-day / total
    # yield / span are derived from the group, never stored here.
    cook_batch_id: UUID | None = None

    class Fields(BaseEntity.Fields):
        RECIPE = "recipe"
        SCHEDULED_FOR = "scheduled_for"
        SERVINGS = "servings"
        SLOT = "slot"
        CONSUMED_AT = "consumed_at"
        COOK_BATCH_ID = "cook_batch_id"
