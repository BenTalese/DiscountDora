from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class StockGroup(BaseEntity):
    name: str

    class Fields(BaseEntity.Fields):
        NAME = "name"
