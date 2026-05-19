from dataclasses import dataclass
from datetime import datetime

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class ProductOffer(BaseEntity):
    OFFERED_ON = "offered_on"
    offered_on: datetime

    PRICE_NOW = "price_now"
    price_now: float

    PRICE_WAS = "price_was"
    price_was: float

    # TODO: Presentation only: calculate save amount, save percentage, per unit price
