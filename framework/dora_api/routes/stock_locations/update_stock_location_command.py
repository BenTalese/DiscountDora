from dataclasses import dataclass

from clapy import AttributeChangeTracker


@dataclass
class UpdateStockLocationCommand:
    name: AttributeChangeTracker[str] = AttributeChangeTracker[str]()
