from dataclasses import dataclass
from uuid import UUID


@dataclass
class CreateStockLocationCommand():
    description: str