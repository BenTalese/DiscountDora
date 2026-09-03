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
    # Owner, 2026-09-04 — a batch-cooking household still cooks some meals on
    # the day: *"I batch cook and freeze lunches for the week, but dinner with
    # the parents on Saturday is fresh."* A fresh meal stands outside the
    # cooked-portion pool in both directions: it never spends a portion
    # (`allocate_pool` skips it, so it can't read as "already covered") and it
    # never asks the pool for one (`recipe_shortfalls` leaves it out of the
    # committed total, and the reconcile sweep doesn't decrement on its day).
    # It is still a cook — just one nobody has to batch for. Mutually exclusive
    # with `cook_batch_id`: a batch IS the pool, so a member of one cannot be
    # fresh. Meaningless when the install's cook-style is "fresh" (every meal
    # is), which is why the UI hides the control there.
    cook_fresh: bool = False

    class Fields(BaseEntity.Fields):
        RECIPE = "recipe"
        SCHEDULED_FOR = "scheduled_for"
        SERVINGS = "servings"
        SLOT = "slot"
        CONSUMED_AT = "consumed_at"
        COOK_BATCH_ID = "cook_batch_id"
        COOK_FRESH = "cook_fresh"
