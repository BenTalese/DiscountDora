"""The anchor key of a shopping-list line.

A line is anchored by a stock item, a product, or (nested product line) both —
`ck_shopping_list_line_anchor` forbids neither. Any dedupe that keys on
`stock_item_id` alone treats every product-only line (NULL item id) as a
duplicate of every other, which is how *Move unticked to a new list* skipped
them all (finalisation 03-R3). Key on the pair instead, through this one helper.
"""
from uuid import UUID

from dora_api.domain.entities.shopping_list import ShoppingListLine


def line_anchor_key(line: ShoppingListLine) -> tuple[UUID | None, UUID | None]:
    return (line.stock_item_id, line.product_id)
