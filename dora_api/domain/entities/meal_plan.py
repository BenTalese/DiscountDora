from dataclasses import dataclass
from datetime import date
from typing import List

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

    class Fields(BaseEntity.Fields):
        ENTRIES = "entries"
        NAME = "name"
        START_DATE = "start_date"
