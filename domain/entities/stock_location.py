from dataclasses import dataclass

from domain.entities.base_entity import BaseEntity


@dataclass
class StockLocation(BaseEntity):
    description: str = None
