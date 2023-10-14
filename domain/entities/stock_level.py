from dataclasses import dataclass

from domain.entities.base_entity import BaseEntity


@dataclass
class StockLevel(BaseEntity):
    description: str = None
