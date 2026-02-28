from dataclasses import dataclass
import logging
from typing import List
from uuid import UUID

from varname import nameof

from dora_api.domain.entities.product import Product
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.decorators import has_response
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class ProductDto:
    brand: str | None
    image: str | None
    is_active: bool
    is_available: bool
    merchant_id: UUID
    merchant_name: str
    merchant_stockcode: str | None
    name: str
    price_now: float
    price_was: float
    product_id: UUID
    size: str
    size_unit: str
    size_value: float
    web_url: str | None

    @classmethod
    def from_entity(cls, product: Product) -> 'ProductDto':
        return ProductDto(
            brand = product.brand,
            # HACK: The Get Products use case decode fails.
            # 'ignore' is a hack solution to temporarily ignore the decoding errors.
            # The My Products/Favorites page will need to address this issue.
            image = product.image.decode('utf-8', 'ignore') if product.image else None,
            is_active = product.is_active,
            is_available = product.is_available,
            merchant_id = product.merchant.id.value,
            merchant_name = product.merchant.name,
            merchant_stockcode = product.merchant_stockcode,
            name = product.name,
            price_now = product.current_offer.price_now,
            price_was = product.current_offer.price_was,
            product_id = product.id.value,
            size = product.size,
            size_unit = product.size_unit,
            size_value = product.size_value,
            web_url = product.web_url
        )


class GetProductsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> List[ProductDto]:
        return (
            self.repository
            .get(Product)
            .include(nameof(Product.current_offer))
            .include(nameof(Product.merchant))
            .project(ProductDto.from_entity)
        )


@PRODUCT_ROUTER.route("")
@PRODUCT_ROUTER.route("<query>")
@has_response(ProductDto)
def get_products(query: str | None = None):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to get products.")
    _Handler = get_container().inject(GetProductsHandler)
    _Result = _Handler.handle()
    _Logger.info(f"Successfully retrieved {len(_Result)} products.")
    return ok(_Result)
