from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class CookBatch(BaseEntity):
    """PROPOSAL_MEAL_PLANS_PART_2 — a *planned* single cook whose output is eaten
    across several linked `MealPlanEntry` rows (same recipe + slot, distinct days):
    "cook X once on the earliest day, eat it Mon+Tue+Wed dinner."

    Deliberately thin. **Cook-day, total yield and span are all DERIVED** from the
    batch's entries (R-003 / state-ownership) and never stored — see
    `get_meal_plans.MealPlanDto`. The entity is first-class for *identity*, FK
    *integrity*, the *demand-collapse* (one cook counted once for ingredient/cost
    demand, not N meals) and future *cross-week* span — not for its column count.

    NOT to be confused with (see the proposal §1):
      * `CookEvent` — a retrospective log of a cook that already happened;
      * `Recipe.available_meals` — the retrospective on-hand cooked-portion pool.
    This is the prospective *plan*.
    """
    meal_plan_id: UUID
    recipe_id: UUID

    class Fields(BaseEntity.Fields):
        MEAL_PLAN_ID = "meal_plan_id"
        RECIPE_ID = "recipe_id"
