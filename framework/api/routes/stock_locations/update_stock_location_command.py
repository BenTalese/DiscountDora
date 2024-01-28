from dataclasses import dataclass

from application.infrastructure.attribute_change_tracker import \
    AttributeChangeTracker


@dataclass
class UpdateStockLocationCommand:
    description: AttributeChangeTracker[str] = AttributeChangeTracker[str]()
