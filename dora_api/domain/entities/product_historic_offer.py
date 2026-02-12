from dataclasses import dataclass
from datetime import datetime

from domain.entities.base_entity import BaseEntity


@dataclass
class ProductHistoricOffer(BaseEntity):
    offered_on: datetime = None
    price_now: float = None
    price_was: float = None
