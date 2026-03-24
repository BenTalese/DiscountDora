from dataclasses import dataclass
from uuid import UUID


@dataclass
class ProductModel:
    brand: str
    image: bytes
    is_available: bool
    merchant_id: UUID
    merchant_stockcode: str
    name: str
    price_now: float
    price_was: float
    product_id: UUID
    size_unit: str
    size_value: float
    web_url: str
