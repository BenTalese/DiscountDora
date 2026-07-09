from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class MealPlanSwapLedger(BaseEntity):
    """FU-451 — append-only record of an applied budget-defense swap, so undo
    is deterministic and audit-visible (proposal §7c). Undo reads
    ``payload_json`` and reverses; no soft-delete state on the mutated row
    itself (Charter P7 — undo is a fresh reverse action, not a hidden flag).

    ``payload_json`` freezes the pre-apply state — enough to rebuild the row
    that changed. Recipe swap: ``{"entry_id", "from_recipe_id", "from_servings"}``.
    (Product swap deferred — see FU-516.)
    """
    meal_plan_id: UUID
    applied_by_user_id: UUID | None
    applied_at: datetime
    kind: str                       # "recipe" | "product"
    payload_json: str
    undone: bool = False
    undone_at: datetime | None = None

    class Fields(BaseEntity.Fields):
        MEAL_PLAN_ID = "meal_plan_id"
        APPLIED_BY_USER_ID = "applied_by_user_id"
        APPLIED_AT = "applied_at"
        KIND = "kind"
        PAYLOAD_JSON = "payload_json"
        UNDONE = "undone"
        UNDONE_AT = "undone_at"
