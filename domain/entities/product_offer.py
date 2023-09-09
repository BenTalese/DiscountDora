import datetime
import uuid


class ProductOffer:
    def __init__(
            self,
            id: uuid,
            price_now: float,
            price_was: float,
            scanned_on_utc: datetime):
        self.id = id
        self.price_now = price_now
        self.price_was = price_was
        self.scanned_on_utc = scanned_on_utc
