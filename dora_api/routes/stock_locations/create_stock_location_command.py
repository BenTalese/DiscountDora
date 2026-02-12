from dataclasses import dataclass


@dataclass
class CreateStockLocationCommand:
    name: str
