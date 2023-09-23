from dataclasses import dataclass
import uuid


@dataclass
class StockLocation:
    id: uuid
    description: str
