from dataclasses import dataclass
from datetime import date
from typing import List

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry


@dataclass
class MealPlan(BaseEntity):
    ENTRIES = "entries"
    entries: List[MealPlanEntry]

    NAME = "name"
    name: str

    START_DATE = "start_date"
    start_date: date
