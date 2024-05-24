from dataclasses import dataclass

from domain.entities.base_entity import BaseEntity


@dataclass
class StockLevel(BaseEntity):
    description: str = None # TODO: change all description properties to "name"
    sequence: int = None
