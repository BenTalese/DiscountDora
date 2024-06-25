from dataclasses import dataclass
from uuid import UUID


@dataclass
class DoraProduct:
    brand: str
    image: bytes
    is_active: bool
    is_available: bool
    merchant_id: UUID
    merchant_name: str
    merchant_stockcode: str
    name: str
    price_now: float
    price_was: float
    product_id: UUID
    size: str
    size_unit: str
    size_value: float
    web_url: str
