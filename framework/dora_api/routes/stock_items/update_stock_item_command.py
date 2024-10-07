from dataclasses import dataclass
from uuid import UUID
from typing import List

from clapy import AttributeChangeTracker


@dataclass
class UpdateStockItemCommand:
    name: str
    product_ids_to_add: AttributeChangeTracker[List[UUID]]
    product_ids_to_remove: AttributeChangeTracker[List[UUID]]
    stock_item_id: UUID
    stock_level_id: AttributeChangeTracker[UUID]
    stock_location_id: AttributeChangeTracker[UUID]
