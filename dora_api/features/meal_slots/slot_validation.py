"""Shared write-time meal-slot validation (C-2.A, R-003 / R-010).

`MealPlanEntry.slot` and `Recipe.time_of_day` hold the slot *name* as free
text (no FK). New writes must match the household `MealSlot` vocabulary; any
legacy/off-vocab string already stored is preserved (deleting a slot leaves
those labels intact). The vocabulary + its validation live on the server only
— callers ask here rather than re-deriving the allowed set.
"""
from typing import Iterable

from dora_api.domain.entities.meal_slot import MealSlot
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


def get_valid_slot_names(repository: SqlAlchemyRepository) -> set[str]:
    """The current household meal-slot vocabulary, as the set of names."""
    return {s.name for s in repository.get(MealSlot).all()}


def find_invalid_slot(names: Iterable[str], valid: set[str]) -> str | None:
    """Return the first name not in the vocabulary, or None if all are valid."""
    for name in names:
        if name not in valid:
            return name
    return None


def invalid_slot_message(name: str, valid: set[str]) -> str:
    return (
        f"Invalid meal slot '{name}'. "
        f"Allowed: {', '.join(sorted(valid))}."
    )
