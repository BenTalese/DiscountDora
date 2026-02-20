from dataclasses import dataclass

from domain.entities.base_entity import BaseEntity


@dataclass(slots=True)
class StockLevel(BaseEntity):
    name: str
    sequence: int
