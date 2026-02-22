from dataclasses import dataclass
from typing import List

from domain.entities.base_entity import BaseEntity
from domain.entities.merchant import Merchant
from domain.entities.product_historic_offer import ProductHistoricOffer
from domain.entities.product_offer import ProductOffer


@dataclass(slots=True)
class Product(BaseEntity):
    brand: str | None
    current_offer: ProductOffer
    historic_offers: List[ProductHistoricOffer]
    image: bytes | None
    is_active: bool
    is_available: bool
    merchant: Merchant
    merchant_stockcode: str | None
    name: str
    size: str
    size_unit: str
    size_value: float | None
    web_url: str | None
