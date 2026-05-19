from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class StockLevel(BaseEntity):
    NAME = "name"
    name: str

    SEQUENCE = "sequence"
    sequence: int
