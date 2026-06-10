from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class Tool(BaseEntity):
    """User-configurable kitchen-tool vocabulary (C-4 Chunk 5). Recipes link
    to tools many-to-many (e.g. food processor, frypan, 5L pot); the set is
    seeded with defaults and edited in settings."""
    name: str
    sequence: int

    class Fields(BaseEntity.Fields):
        NAME = "name"
        SEQUENCE = "sequence"
