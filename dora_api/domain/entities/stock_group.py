from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class StockGroup(BaseEntity):
    name: str
