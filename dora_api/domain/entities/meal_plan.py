from dataclasses import dataclass
from datetime import date
from typing import List
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry


@dataclass
class MealPlan(BaseEntity):
    entries: List[MealPlanEntry]
    # Instances no longer carry a user-facing name (C-2.E) — the planner shows
    # "Week starting <date>". Kept nullable for back-compat / log readability;
    # templates (a separate entity) keep their name.
    name: str | None
    start_date: date
    # provenance: the template this week was forked from, if any. A
    # plain id (not a DB FK) — editing/deleting the template never touches the
    # plan (Decision 1); the UI uses it only for a "re-apply" affordance.
    source_template_id: UUID | None = None
    # provenance when forked from a rotating template *set*:
    # `source_template_set_id` + which item in the set applied to this week.
    source_template_set_id: UUID | None = None
    rotation_index: int | None = None

    class Fields(BaseEntity.Fields):
        ENTRIES = "entries"
        NAME = "name"
        START_DATE = "start_date"
        SOURCE_TEMPLATE_ID = "source_template_id"
        SOURCE_TEMPLATE_SET_ID = "source_template_set_id"
        ROTATION_INDEX = "rotation_index"
