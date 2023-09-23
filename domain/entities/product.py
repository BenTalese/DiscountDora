from dataclasses import dataclass
import uuid
from typing import List

from domain.entities.merchant import Merchant
from domain.entities.product_offer import ProductOffer


@dataclass
class Measurement: # TODO: This should be owned in DB
    id: uuid
    quantity: int
    type: str
    unit: str

@dataclass
class Product:
    id: uuid
    brand: str
    isAvailable: bool
    measurement: Measurement
    merchant: Merchant
    name: str
    offers: List[ProductOffer]
    url: str
