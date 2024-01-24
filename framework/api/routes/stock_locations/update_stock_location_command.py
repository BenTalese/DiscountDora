from dataclasses import dataclass
from uuid import UUID
from application.infrastructure.attribute_change_tracker import \
    AttributeChangeTracker

@dataclass
class UpdateStockLocationCommand:
    description: AttributeChangeTracker[str] = AttributeChangeTracker[str] 
    stock_location_id: UUID
