from dataclasses import dataclass
import uuid


@dataclass
class StockLocation:
    id: uuid = None
    description: str = None
