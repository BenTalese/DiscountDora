from dataclasses import dataclass

from domain.entities.base_entity import BaseEntity


@dataclass(slots=True)
class StockLocation(BaseEntity):
    name: str
