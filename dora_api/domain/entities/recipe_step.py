from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class RecipeStep(BaseEntity):
    """C-4 Chunk 6 — one step (or sub-step) of a structured recipe.

    The self-referential `parent_step_id` gives exactly one level of
    sub-steps: a top-level step has `parent_step_id is None`; a sub-step
    points at its parent. Validation rejects a sub-step whose parent is
    itself a sub-step (no depth > 1) — see the access helpers.

    Ingredient + tool links live in association tables
    (`RecipeStepIngredient`, `RecipeStepTool`); the entity intentionally
    doesn't hold them so the SQLAlchemy mapping stays minimal. DTOs
    surface them as id lists hydrated by `recipe_step_access`.
    """
    recipe_id: UUID
    parent_step_id: UUID | None
    sequence: int
    text: str
    hint: str | None

    class Fields(BaseEntity.Fields):
        RECIPE_ID = "recipe_id"
        PARENT_STEP_ID = "parent_step_id"
        SEQUENCE = "sequence"
        TEXT = "text"
        HINT = "hint"
