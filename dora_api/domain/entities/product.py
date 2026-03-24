from dataclasses import dataclass
from typing import List

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product_historic_offer import \
    ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer


@dataclass
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
    size_value: float
    web_url: str | None
