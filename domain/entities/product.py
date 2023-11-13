from dataclasses import dataclass
from typing import List

from domain.entities.base_entity import BaseEntity
from domain.entities.merchant import Merchant
from domain.entities.product_offer import ProductOffer


@dataclass
class Product(BaseEntity):
    brand: str = None
    current_offer: ProductOffer = None
    historical_offers: List[ProductOffer] = None
    image: bytes = None
    is_available: bool = None
    merchant: Merchant = None
    merchant_stockcode: str = None
    name: str = None
    size_unit: str = None
    size_value: float = None
    web_url: str = None
