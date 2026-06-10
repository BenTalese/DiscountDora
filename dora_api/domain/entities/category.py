from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class Category(BaseEntity):
    """User-configurable recipe category vocabulary (C-4 Chunk 2). Distinct
    from cuisine (L235) — a recipe carries at most one category via an FK."""
    name: str
    sequence: int

    class Fields(BaseEntity.Fields):
        NAME = "name"
        SEQUENCE = "sequence"
