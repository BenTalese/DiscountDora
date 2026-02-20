from dataclasses import dataclass
from datetime import datetime

from domain.entities.base_entity import BaseEntity


@dataclass(slots=True)
class ProductHistoricOffer(BaseEntity):
    offered_on: datetime
    price_now: float
    price_was: float
