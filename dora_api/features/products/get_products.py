import logging
from dataclasses import dataclass
from uuid import UUID

from flask import request
from sqlalchemy import select

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import bad_request, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.infrastructure.utils import get_container
from dora_api.app import db
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Non-frozen so we can stamp `linked_stock_item_*` on after the page comes
# back. Cheaper than re-running pagination through a richer entity load,
# and keeps `from_entity` honest about what's straight from the Product row.
@dataclass(slots=True)
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
    # Stamped in `GetProductsHandler.handle` after pagination. A product is
    # one stock item's responsibility (StockItemProduct's PK is (stock_item,
    # product)), but we keep it nullable for orphan products and for the
    # "unlinked" state.
    linked_stock_item_id: UUID | None = None
    linked_stock_item_name: str | None = None

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
            web_url = product.web_url,
        )


_FIELD_MAP: dict[str, EntityField] = {
    "product_id": EntityField(Product, "id"),
    "merchant_id": EntityField(Product, "_merchant_id"),
}


class GetProductsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, options) -> Page[ProductDto]:
        page = (
            self.repository
            .get(Product)
            .include(Product.Fields.CURRENT_OFFER)
            .include(Product.Fields.MERCHANT)
            .paginate(options, ProductDto.from_entity, field_map=_FIELD_MAP)
        )
        # ── Enrich with the linked stock item ────────────────────────
        # One bulk query against the m2m join, then a single StockItem
        # lookup for the names. The whole product page is in memory and
        # this side-trip is two indexed reads — well within budget.
        if page.items:
            product_ids = [p.product_id for p in page.items]
            assoc = db.metadata.tables["StockItemProduct"]
            session = self.repository.session
            rows = session.execute(
                select(assoc.c.product_id, assoc.c.stock_item_id)
                .where(assoc.c.product_id.in_(product_ids))
            ).all()
            product_to_stock: dict[UUID, UUID] = {row[0]: row[1] for row in rows}
            stock_ids = list({sid for sid in product_to_stock.values()})
            stock_lookup: dict[UUID, StockItem] = {}
            if stock_ids:
                items = self.repository.get(StockItem).all(
                    EntityField(StockItem, "id").in_(stock_ids)
                )
                stock_lookup = {s.id: s for s in items}
            for dto in page.items:
                stock_id = product_to_stock.get(dto.product_id)
                if stock_id is None:
                    continue
                dto.linked_stock_item_id = stock_id
                item = stock_lookup.get(stock_id)
                dto.linked_stock_item_name = item.name if item else None
        return page


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
