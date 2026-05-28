from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


# Sentinel reasons — plain str so SQLAlchemy stores varchar, matching the
# ADDED_VIA_* pattern on ShoppingListLine. Anything outside this set is
# rejected at the request layer (the entity itself stays permissive so a
# future reason added in a newer install doesn't blow up an older API).
WASTE_REASON_EXPIRED = "expired"
WASTE_REASON_SPOILED = "spoiled"
WASTE_REASON_DID_NOT_LIKE = "did_not_like"
WASTE_REASON_OVERBOUGHT = "overbought"
WASTE_REASON_OTHER = "other"

WASTE_REASON_VALUES = {
    WASTE_REASON_EXPIRED,
    WASTE_REASON_SPOILED,
    WASTE_REASON_DID_NOT_LIKE,
    WASTE_REASON_OVERBOUGHT,
    WASTE_REASON_OTHER,
}


@dataclass
class StockItemWasteEvent(BaseEntity):
    """P2-06 — append-only log of food the household discarded.

    Optional in every sense: the user only writes a row when they
    actively tell Dora "I had to throw this out". Feeds the waste
    insights tool ("what am I wasting often?") and the per-item history
    on the stock detail view.

    `stock_item_name` is denormalised so insights survive a stock item
    being renamed or deleted. The FK is SET NULL on delete; we keep the
    history rather than cascade-deleting it.
    `estimated_value` is per-event total (not per-unit) — captured at
    log time, usually pre-filled from the user's recent purchase price
    so the SPA doesn't need a live lookup at view time.
    """
    stock_item_id: UUID | None
    stock_item_name: str
    reason: str
    quantity: int | None
    estimated_value: float | None
    note: str | None
    occurred_at: datetime

    class Fields(BaseEntity.Fields):
        STOCK_ITEM_ID = "stock_item_id"
        STOCK_ITEM_NAME = "stock_item_name"
        REASON = "reason"
        QUANTITY = "quantity"
        ESTIMATED_VALUE = "estimated_value"
        NOTE = "note"
        OCCURRED_AT = "occurred_at"
