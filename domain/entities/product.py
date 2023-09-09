from typing import List
import uuid

from domain.entities.merchant import Merchant
from domain.entities.product_offer import ProductOffer


class Measurement: # TODO: This should be owned in DB
    def __init__(
            self,
            id: uuid,
            quantity: int,
            type: str,
            unit: str):
        self.id = id
        quantity = quantity
        type = type
        unit = unit

class Product:
    def __init__(
            self,
            id: uuid,
            brand: str,
            isAvailable: bool,
            measurement: Measurement,
            merchant: Merchant,
            name: str,
            offers: List[ProductOffer],
            url: str):
        self.id = id
        self.brand = brand
        self.isAvailable = isAvailable
        self.measurement = measurement
        self.merchant = merchant
        self.name = name
        self.offers = offers
        self.url = url
