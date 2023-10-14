from dataclasses import dataclass
import datetime

from domain.entities.base_entity import BaseEntity


@dataclass
class ProductOffer(BaseEntity):
    price_now: float = None
    price_was: float = None
    scanned_on_utc: datetime = None
