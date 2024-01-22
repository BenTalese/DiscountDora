from dataclasses import dataclass


@dataclass
class CreateStockLocationCommand:
    description: str
