from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class StockLevelChange(BaseEntity):
    """Append-only log of a stock item's level transitions.

    The level name is denormalised so the history survives a StockLevel
    being renamed or deleted (the FK is SET NULL on delete).
    """
    stock_item_id: UUID
    stock_level_id: UUID | None
    stock_level_name: str | None
    changed_at: datetime

    class Fields(BaseEntity.Fields):
        STOCK_ITEM_ID = "stock_item_id"
        STOCK_LEVEL_ID = "stock_level_id"
        STOCK_LEVEL_NAME = "stock_level_name"
        CHANGED_AT = "changed_at"
