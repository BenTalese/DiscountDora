from dataclasses import dataclass
from datetime import datetime

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class IdempotencyKey(BaseEntity):
    """A consumed `Idempotency-Key` from a `POST /api/ingest` batch
    (PROPOSAL_INGESTION_API §2.3). Re-sends of the same key short-circuit
    to a no-op; the TTL (`expires_at`) lets old entries age out so the
    table stays bounded.
    """
    key: str
    source_id: str  # UUID-as-text — the IngestionSource scope
    expires_at: datetime
    created_at: datetime

    class Fields(BaseEntity.Fields):
        KEY = "key"
        SOURCE_ID = "source_id"
        EXPIRES_AT = "expires_at"
        CREATED_AT = "created_at"
