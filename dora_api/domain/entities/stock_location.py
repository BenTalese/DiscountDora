from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


# Hierarchy kinds. Depth is enforced by the application: a "zone" has no
# parent, an "area" has a zone parent, a "section" has an area parent.
LOCATION_KIND_ZONE = "zone"
LOCATION_KIND_AREA = "area"
LOCATION_KIND_SECTION = "section"
ALLOWED_LOCATION_KINDS = (LOCATION_KIND_ZONE, LOCATION_KIND_AREA, LOCATION_KIND_SECTION)


@dataclass
class StockLocation(BaseEntity):
    NAME = "name"
    name: str

    KIND = "kind"
    kind: str = LOCATION_KIND_ZONE

    PARENT_ID = "parent_id"
    parent_id: UUID | None = None

    SEQUENCE = "sequence"
    sequence: int = 0
    # NOTE: children are NOT a dataclass field — they're loaded manually by
    # repository queries (matching the codebase's noload+manual fetch
    # pattern) and assembled into a tree by the get_location_tree handler.
    # Adding them as a field would force verify_mappings() to demand a
    # SQLAlchemy relationship, which we don't want for self-referential
    # imperative mapping reasons.
