from dataclasses import dataclass
import datetime

from domain.entities.base_entity import BaseEntity


@dataclass
class ProductOffer(BaseEntity):
    offered_on: datetime = None
    price_now: float = None
    price_was: float = None
    # TODO: Presentation only: calculate save amount, save percentage, per unit price
