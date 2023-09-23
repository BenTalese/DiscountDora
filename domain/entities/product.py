from dataclasses import dataclass
import uuid
from typing import List

from domain.entities.merchant import Merchant
from domain.entities.product_offer import ProductOffer


@dataclass
class Measurement: # TODO: This should be owned in DB
    id: uuid = None
    quantity: int = None
    type: str = None
    unit: str = None

@dataclass
class Product:
    id: uuid = None
    brand: str = None
    isAvailable: bool = None
    measurement: Measurement = None
    merchant: Merchant = None
    name: str = None
    offers: List[ProductOffer] = None
    url: str = None
