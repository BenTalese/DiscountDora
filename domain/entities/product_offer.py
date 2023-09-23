from dataclasses import dataclass
import datetime
import uuid


@dataclass
class ProductOffer:
    id: uuid
    price_now: float
    price_was: float
    scanned_on_utc: datetime
