from dataclasses import dataclass
from datetime import datetime

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class StockMap(BaseEntity):
    """Hand-drawn pantry layout. JSON blob, structure owned by the
    frontend — see web_app/src/pages/StockMap.vue for the schema. The
    backend is intentionally dumb here: it stores and serves the blob
    verbatim, so canvas-side iteration doesn't need a backend round
    every time the SPA wants to add a new field.
    """
    layout: str       # JSON-encoded blob
    updated_at: datetime

    class Fields(BaseEntity.Fields):
        LAYOUT = "layout"
        UPDATED_AT = "updated_at"
