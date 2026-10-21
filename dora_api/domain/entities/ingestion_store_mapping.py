from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class IngestionStoreMapping(BaseEntity):
    """Maps an external producer's store name onto a Dora-side `Store`
    (FU-190 / PROPOSAL_PRODUCTS_AS_OVERLAY §3.3).

    The ingest endpoint **never auto-creates stores**. For each
    record's `store` value, this table resolves it to a Dora
    `Store`. Two states:

    - **mapped** (`store_id` set) — accepted records use this store.
    - **quarantined** (`store_id` is None) — the producer pushed an
      external name we've never seen; the record is skipped and the
      pending mapping is surfaced on the API access page so the admin
      can either link it to an existing store or create one.
    """
    source_id: UUID
    external_name: str
    store_id: UUID | None
    created_at: datetime
    last_seen_at: datetime | None = None

    class Fields(BaseEntity.Fields):
        SOURCE_ID = "source_id"
        EXTERNAL_NAME = "external_name"
        STORE_ID = "store_id"
        CREATED_AT = "created_at"
        LAST_SEEN_AT = "last_seen_at"
