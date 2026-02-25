from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass(slots=True)
class Merchant(BaseEntity):
    name: str
    # url: str = None # hmm...does this belong in this domain?
