from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class Cuisine(BaseEntity):
    """User-configurable recipe cuisine vocabulary (C-4 Chunk 2). A recipe
    carries at most one cuisine via an FK; the set is seeded with defaults
    and edited in settings."""
    name: str
    sequence: int

    class Fields(BaseEntity.Fields):
        NAME = "name"
        SEQUENCE = "sequence"
