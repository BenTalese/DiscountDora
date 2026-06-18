from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class Store(BaseEntity):
    """A user-curated retail store (FU-189). Replaces the former `Merchant`
    entity post-Phase-E. Users curate the list themselves — Dora ships zero
    prefilled stores and never auto-creates one (no-auto-create rule, see
    FU-190). Stores optionally carry a user-uploaded logo (`image`); the SPA
    falls back to a hash-swatch + initial when none is set."""
    name: str
    image: bytes | None = None

    class Fields(BaseEntity.Fields):
        NAME = "name"
        IMAGE = "image"
