from dataclasses import dataclass
from uuid import UUID

@dataclass
class DeleteStockLocationCommand:
    stock_location_id: UUID
