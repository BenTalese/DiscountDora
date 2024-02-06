from dataclasses import dataclass

from clapy import AttributeChangeTracker


@dataclass
class UpdateStockLocationCommand:
    description: AttributeChangeTracker[str] = AttributeChangeTracker[str]()
