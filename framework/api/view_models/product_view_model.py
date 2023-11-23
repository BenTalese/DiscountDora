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
    merchant_stockcode: str
    name: str
    price_now: float
    price_was: float
    product_id: UUID # FIXME: Fix uuid and datetime types everywhere, should be from datetime and from uuid, not modules themselves
    size_unit: str
    size_value: float
    web_url: str

def get_product_view_model(product: ProductDto) -> ProductViewModel:
    return ProductViewModel(
        brand = product.brand,
        image = product.image.decode('utf-8'),
        is_available = product.is_available,
        merchant_id = product.merchant_id,
        merchant_stockcode = product.merchant_stockcode,
        name = product.name,
        price_now = product.current_offer.price_now,
        price_was = product.current_offer.price_was,
        product_id = product.id.value,
        size_unit = product.size_unit,
        size_value = product.size_value,
        web_url = product.web_url
    )
