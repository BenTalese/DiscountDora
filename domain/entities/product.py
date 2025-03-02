from dataclasses import dataclass
from typing import List

from domain.entities.base_entity import BaseEntity
from domain.entities.merchant import Merchant
from domain.entities.product_historic_offer import ProductHistoricOffer
from domain.entities.product_offer import ProductOffer


@dataclass
class Product(BaseEntity):
    brand: str = None
    current_offer: ProductOffer = None
    historic_offers: List[ProductHistoricOffer] = None
    image: bytes = None
    is_active: bool = None
    is_available: bool = None
    merchant: Merchant = None
    merchant_stockcode: str = None
    name: str = None
    size: str = None
    size_unit: str = None
    size_value: float = None
    web_url: str = None
