"""Templates for shopping lists.

A template is a saved list shape that can be instantiated into a fresh
shopping list (or merged into an existing one). Templates carry no
ticked/archived/primary state — they're just a name + a set of stock
items with default quantities.

Per-line product selection (`selected_product_id`) is intentionally
omitted from templates: deals shift, and saving "I bought the Coles one
last time" into a template tends to age badly. The instantiated list
falls back to the cheapest-available-offer auto-pick at use time.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class ShoppingListTemplateLine(BaseEntity):
    template_id: UUID
    stock_item_id: UUID
    quantity: int | None = 1
    sequence: int = 0

    class Fields(BaseEntity.Fields):
        TEMPLATE_ID = "template_id"
        STOCK_ITEM_ID = "stock_item_id"
        QUANTITY = "quantity"
        SEQUENCE = "sequence"


@dataclass
class ShoppingListTemplate(BaseEntity):
    name: str
    created_at: datetime
    updated_at: datetime
    lines: List[ShoppingListTemplateLine] = field(default_factory=list)

    class Fields(BaseEntity.Fields):
        NAME = "name"
        CREATED_AT = "created_at"
        UPDATED_AT = "updated_at"
        LINES = "lines"
