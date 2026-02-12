from dataclasses import dataclass

from domain.entities.base_entity import BaseEntity


@dataclass
class Merchant(BaseEntity):
    name: str = None
    # url: str = None # hmm...does this belong in this domain?
