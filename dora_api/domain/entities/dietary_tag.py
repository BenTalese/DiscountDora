from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class DietaryTag(BaseEntity):
    """User-configurable dietary / allergen-free / nutritional tag vocabulary
    (C-4 Chunk 2). Replaces the in-code `recipe_tags.py` catalogue. Recipes
    link to these many-to-many via the `RecipeTag` association.

    `category` groups tags in the picker (e.g. "Allergen-free"); it's a plain
    grouping label, not an FK to the recipe Category vocabulary."""
    name: str
    category: str
    sequence: int

    class Fields(BaseEntity.Fields):
        NAME = "name"
        CATEGORY = "category"
        SEQUENCE = "sequence"
