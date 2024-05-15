from dataclasses import dataclass


@dataclass
class CreateProductCommand:
    brand: str
    image: bytes
    is_active: bool
    is_available: bool
    merchant_name: str
    merchant_stockcode: str
    name: str
    price_now: float
    price_was: float
    size: str
    size_unit: str
    size_value: float
    web_url: str
