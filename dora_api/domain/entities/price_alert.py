from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class PriceAlert(BaseEntity):
    """Per-user "tell me when this product hits $X" subscription.

    `last_fired_at` tracks the most recent notification so the alert
    worker doesn't double-notify on consecutive cheap scrapes. The
    expected behaviour: re-arm only when the price climbs back above
    the threshold and then drops again. The trigger-side logic lives in
    the scrape pipeline (out of scope for the explorer page itself).
    """
    user_id: UUID
    product_id: UUID
    threshold_unit_price: float
    created_at: datetime
    last_fired_at: datetime | None = None

    class Fields(BaseEntity.Fields):
        USER_ID = "user_id"
        PRODUCT_ID = "product_id"
        THRESHOLD_UNIT_PRICE = "threshold_unit_price"
        CREATED_AT = "created_at"
        LAST_FIRED_AT = "last_fired_at"
