from dataclasses import dataclass
from uuid import UUID

from clapy import AttributeChangeTracker


@dataclass
class UpdateStockItemCommand:
    name: AttributeChangeTracker[str]
    stock_level_id: AttributeChangeTracker[UUID]
    stock_location_id: AttributeChangeTracker[UUID]
