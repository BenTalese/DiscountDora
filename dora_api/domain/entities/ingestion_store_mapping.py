from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class IngestionStoreMapping(BaseEntity):
    """Maps an external producer's store/merchant name onto a Dora-side
    `Merchant` (FU-190 / PROPOSAL_PRODUCTS_AS_OVERLAY §3.3).

    The ingest endpoint **never auto-creates merchants**. For each
    record's `merchant` value, this table resolves it to a Dora
    `Merchant`. Two states:

    - **mapped** (`merchant_id` set) — accepted records use this merchant.
    - **quarantined** (`merchant_id` is None) — the producer pushed an
      external name we've never seen; the record is skipped and the
      pending mapping is surfaced on the API access page so the admin
      can either link it to an existing merchant or create one.
    """
    source_id: UUID
    external_name: str
    merchant_id: UUID | None
    created_at: datetime
    last_seen_at: datetime | None = None

    class Fields(BaseEntity.Fields):
        SOURCE_ID = "source_id"
        EXTERNAL_NAME = "external_name"
        MERCHANT_ID = "merchant_id"
        CREATED_AT = "created_at"
        LAST_SEEN_AT = "last_seen_at"
