from dataclasses import dataclass
from uuid import UUID

from domain.entities.product import Product


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
    price_now: float
    price_was: float
    product_id: UUID
    size: str
    size_unit: str
    size_value: float
    web_url: str


# FIXME This is horrible to manage, if any mapping reaches more than one level i need to null check
def get_product_view_model(product: Product) -> ProductViewModel:
    return ProductViewModel(
        brand = product.brand,
        # HACK: The Get Products use case decode fails.
        # 'ignore' is a hack solution to remporarily ignore the decoding errors.
        # The My Products/Favorites page will need to address this issue.
        image = product.image.decode('utf-8', 'ignore') if product.image else None,
        is_active = product.is_active,
        is_available = product.is_available,
        merchant_id = product.merchant.id.value if product.merchant else None,
        merchant_name = product.merchant.name if product.merchant else None,
        merchant_stockcode = product.merchant_stockcode,
        name = product.name,
        price_now = product.current_offer.price_now if product.current_offer else None,
        price_was = product.current_offer.price_was if product.current_offer else None,
        product_id = product.id.value,
        size = product.size,
        size_unit = product.size_unit,
        size_value = product.size_value,
        web_url = product.web_url
    )
