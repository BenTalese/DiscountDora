from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class MealSlot(BaseEntity):
    """Household-wide meal-slot vocabulary (C-2.A). Mirrors the Cuisine vocab
    pattern, but `MealPlanEntry.slot` / `Recipe.time_of_day` hold the slot
    *name* as free-text (no FK) — the table just pins the vocabulary and is
    validated against at write-time. Seeded with the five DEFAULT_MEAL_SLOTS
    and edited in settings."""
    name: str
    sequence: int

    class Fields(BaseEntity.Fields):
        NAME = "name"
        SEQUENCE = "sequence"
