from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


# Append-only receipt states (proposal §7.1). A receipt is never mutated in
# place; corrective decisions write a NEW receipt against the same entry
# (matches `MealPlanSwapLedger`'s shape from FU-451).
STATE_UNRESOLVED_AUTO = "unresolved_auto"
STATE_UNRESOLVED_MANUAL = "unresolved_manual"
STATE_RESOLVED_CONFIRMED = "resolved_confirmed"
STATE_RESOLVED_ADJUSTED = "resolved_adjusted"
STATE_RESOLVED_NOT_COOKED = "resolved_not_cooked"
STATE_RESOLVED_DEFERRED = "resolved_deferred"
RECONCILE_STATE_VALUES = (
    STATE_UNRESOLVED_AUTO,
    STATE_UNRESOLVED_MANUAL,
    STATE_RESOLVED_CONFIRMED,
    STATE_RESOLVED_ADJUSTED,
    STATE_RESOLVED_NOT_COOKED,
    STATE_RESOLVED_DEFERRED,
)


@dataclass
class MealPlanReconcileReceipt(BaseEntity):
    """FU-317 — append-only audit row for a meal-plan reconcile event.

    Chunk 1 writes one receipt per past-day `MealPlanEntry` at daily
    rollover: `unresolved_auto` when the install-wide
    `AppSetting.auto_drain_past_meals` is TRUE (today's silent drain
    plus a receipt the user can dispute), `unresolved_manual` when it
    is FALSE (the pool stays untouched until someone walks the reconcile
    page — proposal §2).

    Chunks 3+ append `resolved_*` receipts as the user acts on the
    reconcile page. `original_servings` freezes the entry's planned
    servings at receipt creation; `actual_servings` is set on
    `resolved_adjusted`; `cooked_on` on later-than-planned resolutions.
    Never mutated in place — a change of mind writes a fresh reverse
    receipt (Charter P4 preservation of trust; matches the
    `MealPlanSwapLedger` idiom from FU-451).
    """
    meal_plan_entry_id: UUID
    state: str
    original_servings: int
    created_at: datetime
    actual_servings: int | None = None
    cooked_on: date | None = None
    resolved_by_user_id: UUID | None = None
    resolved_at: datetime | None = None
    note: str | None = None

    class Fields(BaseEntity.Fields):
        MEAL_PLAN_ENTRY_ID = "meal_plan_entry_id"
        STATE = "state"
        ORIGINAL_SERVINGS = "original_servings"
        ACTUAL_SERVINGS = "actual_servings"
        COOKED_ON = "cooked_on"
        RESOLVED_BY_USER_ID = "resolved_by_user_id"
        RESOLVED_AT = "resolved_at"
        NOTE = "note"
        CREATED_AT = "created_at"
