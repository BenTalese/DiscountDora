from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from application.dtos.product_dto import ProductDto


@dataclass
class ProductViewModel:
    brand: str
    image: bytes
    is_available: bool
    merchant_id: UUID
    merchant_name: str
    merchant_stockcode: str
    name: str
    price_now: float
    price_was: float
    product_id: UUID
    size_unit: str
    size_value: float
    web_url: str

# FIXME This is horrible to manage, if any mapping reaches more than one level i need to null check
def get_product_view_model(product: ProductDto) -> ProductViewModel:
    return ProductViewModel(
        brand = product.brand,
        image = product.image.decode('utf-8'),
        is_available = product.is_available,
        merchant_id = product.merchant.merchant_id.value if product.merchant else None,
        merchant_name = product.merchant.name if product.merchant else None,
        merchant_stockcode = product.merchant_stockcode,
        name = product.name,
        price_now = product.current_offer.price_now if product.current_offer else None,
        price_was = product.current_offer.price_was if product.current_offer else None,
        product_id = product.product_id.value,
        size_unit = product.size_unit,
        size_value = product.size_value,
        web_url = product.web_url
    )
