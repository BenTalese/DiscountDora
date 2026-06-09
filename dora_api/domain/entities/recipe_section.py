from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class RecipeSection(BaseEntity):
    """C-4 Chunk 10 — a named group within a recipe (DEC-3 option A).

    A recipe owns 0..N sections. Ingredients (and steps) carry a nullable
    `section_id`; rows with NULL section_id are the implicit "main" group
    so existing recipes continue to render unchanged without a data
    migration. `sequence` is the display order among the recipe's
    sections; `name` is shown as the group header.
    """
    recipe_id: UUID
    sequence: int
    name: str

    class Fields(BaseEntity.Fields):
        RECIPE_ID = "recipe_id"
        SEQUENCE = "sequence"
        NAME = "name"
