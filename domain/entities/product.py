from dataclasses import dataclass
from typing import List
from domain.entities.base_entity import BaseEntity

from domain.entities.merchant import Merchant
from domain.entities.product_offer import ProductOffer


@dataclass
class Measurement(BaseEntity): # TODO: This should be owned in DB
    quantity: int = None
    type: str = None
    unit: str = None

@dataclass
class Product(BaseEntity):
    brand: str = None
    current_offer: ProductOffer = None # flatten onto Product?
    # historical_offers: List[ProductOffer] = None
    isAvailable: bool = None
    measurement: Measurement = None
    merchant: Merchant = None
    name: str = None
    url: str = None
