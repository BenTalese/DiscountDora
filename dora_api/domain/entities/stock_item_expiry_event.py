from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


# Sentinel event kinds. Kept as plain strings (matching the WasteEvent
# `reason` pattern) so SQLAlchemy stores varchar and older APIs don't
# choke on a newer install adding a kind.
EXPIRY_EVENT_SET = "set"          # First-time set (prev None → new date)
EXPIRY_EVENT_PUSHED = "pushed"    # Both dates present; new > prev by delta_days
EXPIRY_EVENT_CLEARED = "cleared"  # new date None; prev was set

EXPIRY_EVENT_KINDS = {
    EXPIRY_EVENT_SET,
    EXPIRY_EVENT_PUSHED,
    EXPIRY_EVENT_CLEARED,
}


@dataclass
class StockItemExpiryEvent(BaseEntity):
    """Append-only log of expiry-date changes on a stock item.

    Emitted whenever `StockItem.expiry_date` transitions between
    values (see `create_stock_item.py` and `update_stock_item.py`).
    Consumed by the Stock Item detail's History tab — highest signal
    on perishables where a pattern of repeat pushes tells the user
    something.

    `kind` is a coarse label the SPA can style ("Set expiry" /
    "Pushed +7 days" / "Cleared expiry"); `delta_days` is only set on
    `pushed` events. FK is `SET NULL` on delete so history survives.
    """
    stock_item_id: UUID | None
    kind: str
    previous_expiry_date: date | None
    new_expiry_date: date | None
    delta_days: int | None
    occurred_at: datetime

    class Fields(BaseEntity.Fields):
        STOCK_ITEM_ID = "stock_item_id"
        KIND = "kind"
        PREVIOUS_EXPIRY_DATE = "previous_expiry_date"
        NEW_EXPIRY_DATE = "new_expiry_date"
        DELTA_DAYS = "delta_days"
        OCCURRED_AT = "occurred_at"


def classify_expiry_transition(
    previous: date | None,
    new: date | None,
) -> tuple[str, int | None] | None:
    """Map a before→after expiry-date transition to an event kind
    (or `None` when nothing changed). Delta is only meaningful on
    the `pushed` kind — set/cleared return `None` delta.

    Lives on the entity module because it's the single source of
    truth for how the two handlers (create + update) decide what
    to emit. Callers pass their pre/post dates and stamp the event
    from the return value.
    """
    if previous == new:
        return None
    if new is None:
        return (EXPIRY_EVENT_CLEARED, None)
    if previous is None:
        return (EXPIRY_EVENT_SET, None)
    delta = (new - previous).days
    return (EXPIRY_EVENT_PUSHED, delta)
