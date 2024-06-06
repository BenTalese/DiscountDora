from dataclasses import dataclass
from uuid import UUID

from clapy import AttributeChangeTracker


@dataclass
class UpdateStockItemCommand:
    name: str
    stock_item_id: UUID
    stock_level_id: AttributeChangeTracker[UUID]
    stock_location_id: AttributeChangeTracker[UUID]
