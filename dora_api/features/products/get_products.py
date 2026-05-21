import logging
from dataclasses import dataclass
from uuid import UUID

from flask import request

from dora_api.domain.entities.product import Product
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import bad_request, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
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
            merchant_id = product.merchant.id,
            merchant_name = product.merchant.name,
            merchant_stockcode = product.merchant_stockcode,
            name = product.name,
            price_now = product.current_offer.price_now,
            price_was = product.current_offer.price_was,
            product_id = product.id,
            size = product.size,
            size_unit = product.size_unit,
            size_value = product.size_value,
            web_url = product.web_url
        )


_FIELD_MAP: dict[str, EntityField] = {
    "product_id": EntityField(Product, "id"),
    "merchant_id": EntityField(Product, "_merchant_id"),
}


class GetProductsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, options) -> Page[ProductDto]:
        return (
            self.repository
            .get(Product)
            .include(Product.Fields.CURRENT_OFFER)
            .include(Product.Fields.MERCHANT)
            .paginate(options, ProductDto.from_entity, field_map=_FIELD_MAP)
        )


@PRODUCT_ROUTER.route("")
def get_products():
    _Logger = logging.getLogger(__name__)
    try:
        _Options = parse_query_options(request.args)
        _Page = get_container().inject(GetProductsHandler).handle(_Options)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info(f"Retrieved {len(_Page.items)} of {_Page.total} products.")
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)
