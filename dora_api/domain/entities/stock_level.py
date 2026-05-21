from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class StockLevel(BaseEntity):
    name: str
    sequence: int

    class Fields(BaseEntity.Fields):
        NAME = "name"
        SEQUENCE = "sequence"
