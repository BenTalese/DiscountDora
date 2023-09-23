from dataclasses import dataclass
import datetime
import uuid


@dataclass
class ProductOffer:
    id: uuid = None
    price_now: float = None
    price_was: float = None
    scanned_on_utc: datetime = None
