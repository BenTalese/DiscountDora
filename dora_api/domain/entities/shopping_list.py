from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class ShoppingListLine(BaseEntity):
    shopping_list_id: UUID
    stock_item_id: UUID
    quantity: int | None = None
    is_ticked: bool = False
    selected_product_id: UUID | None = None
    sequence: int = 0

    class Fields(BaseEntity.Fields):
        SHOPPING_LIST_ID = "shopping_list_id"
        STOCK_ITEM_ID = "stock_item_id"
        QUANTITY = "quantity"
        IS_TICKED = "is_ticked"
        SELECTED_PRODUCT_ID = "selected_product_id"
        SEQUENCE = "sequence"


@dataclass
class ShoppingList(BaseEntity):
    name: str
    created_at: datetime
    is_primary: bool = False
    is_archived: bool = False
    # `is_in_progress` is the "I'm actively shopping right now" state. While
    # true, the UI locks editing (add/remove lines, rename) and emphasises
    # ticking off. Transitions:
    #   planning    -> in_progress: user clicks Start shopping
    #   in_progress -> planning   : user clicks Stop shopping (no archive)
    #   in_progress -> archived   : user clicks Finish (the finish endpoint
    #                               archives and `is_in_progress` becomes
    #                               irrelevant once archived).
    is_in_progress: bool = False
    completed_at: datetime | None = None
    # Lines hang off the list. Loaded explicitly by handlers that need them
    # (matches the noload pattern used elsewhere — table_mappings sets
    # lazy="noload"). Default empty so seed/in-memory construction works.
    lines: List[ShoppingListLine] = field(default_factory=list)

    class Fields(BaseEntity.Fields):
        NAME = "name"
        IS_PRIMARY = "is_primary"
        IS_ARCHIVED = "is_archived"
        IS_IN_PROGRESS = "is_in_progress"
        CREATED_AT = "created_at"
        COMPLETED_AT = "completed_at"
        LINES = "lines"
