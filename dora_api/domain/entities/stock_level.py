from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass(slots=True)
class StockLevel(BaseEntity):
    name: str
    sequence: int
