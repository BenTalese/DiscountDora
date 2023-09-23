from dataclasses import dataclass
import uuid


@dataclass
class StockLevel:
    id: uuid = None
    description: str = None
