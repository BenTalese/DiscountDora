from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class Merchant(BaseEntity):
    name: str
    # url: str = None # hmm...does this belong in this domain?

    class Fields(BaseEntity.Fields):
        NAME = "name"
