from dataclasses import dataclass
from uuid import UUID


@dataclass
class CreateStockItemCommand:
    name: str
    stock_level_id: UUID
    stock_location_id: UUID
