from base64 import b64decode
from dataclasses import dataclass
from uuid import UUID

from application.dtos.product_dto import ProductDto


@dataclass
class ProductViewModel:
    brand: str
    image: bytes
    is_active: bool
    is_available: bool
    merchant_id: UUID
    merchant_name: str
    merchant_stockcode: str
    name: str
    price_difference: float
    price_now: float
    price_per_cup: str
    price_was: float
    product_id: UUID
    size: str
    size_unit: str
    size_value: float
    web_url: str

# FIXME This is horrible to manage, if any mapping reaches more than one level i need to null check
def get_product_view_model(product: ProductDto) -> ProductViewModel:
    return ProductViewModel(
        brand = product.brand,
        image = product.image.decode(),
        is_active = product.is_active,
        is_available = product.is_available,
        merchant_id = product.merchant.merchant_id.value if product.merchant else None,
        merchant_name = product.merchant.name if product.merchant else None,
        merchant_stockcode = product.merchant_stockcode,
        name = product.name,
        price_difference = product.current_offer.price_difference if product.current_offer else None,
        price_now = product.current_offer.price_now if product.current_offer else None,
        price_per_cup = product.current_offer.price_per_cup if product.current_offer else None,
        price_was = product.current_offer.price_was if product.current_offer else None,
        product_id = product.product_id.value,
        size = product.size,
        size_unit = product.size_unit,
        size_value = product.size_value,
        web_url = product.web_url
    )
