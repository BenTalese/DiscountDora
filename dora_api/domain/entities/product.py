from dataclasses import dataclass
from typing import List

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product_historic_offer import \
    ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer


@dataclass
class Product(BaseEntity):
    BRAND = "brand"
    brand: str | None

    CURRENT_OFFER = "current_offer"
    current_offer: ProductOffer

    HISTORIC_OFFERS = "historic_offers"
    historic_offers: List[ProductHistoricOffer]

    IMAGE = "image"
    image: bytes | None

    IS_ACTIVE = "is_active"
    is_active: bool

    IS_AVAILABLE = "is_available"
    is_available: bool

    MERCHANT_STOCKCODE = "merchant_stockcode"
    merchant_stockcode: str | None

    MERCHANT = "merchant"
    merchant: Merchant

    NAME = "name"
    name: str

    SIZE = "size"
    size: str

    SIZE_UNIT = "size_unit"
    size_unit: str

    SIZE_VALUE = "size_value"
    size_value: float

    WEB_URL = "web_url"
    web_url: str | None
