from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class ShoppingListLine(BaseEntity):
    SHOPPING_LIST_ID = "shopping_list_id"
    shopping_list_id: UUID

    STOCK_ITEM_ID = "stock_item_id"
    stock_item_id: UUID

    IS_TICKED = "is_ticked"
    is_ticked: bool = False

    QUANTITY = "quantity"
    quantity: int | None = None

    SELECTED_PRODUCT_ID = "selected_product_id"
    selected_product_id: UUID | None = None

    SEQUENCE = "sequence"
    sequence: int = 0


@dataclass
class ShoppingList(BaseEntity):
    CREATED_AT = "created_at"
    created_at: datetime

    NAME = "name"
    name: str

    # Lines hang off the list. Loaded explicitly by handlers that need them
    # (matches the noload pattern used elsewhere — table_mappings sets
    # lazy="noload"). Default empty so seed/in-memory construction works.
    LINES = "lines"
    lines: List[ShoppingListLine] = field(default_factory=list)

    COMPLETED_AT = "completed_at"
    completed_at: datetime | None = None

    IS_ARCHIVED = "is_archived"
    is_archived: bool = False

    IS_PRIMARY = "is_primary"
    is_primary: bool = False
