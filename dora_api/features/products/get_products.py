import logging
from dataclasses import dataclass
from uuid import UUID

from flask import request
from sqlalchemy import select

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.product_offer import discount_percent
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import bad_request, ok, paginated
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
    # bytes never travel in list/detail JSON. SPA fetches via
    # `GET /products/<id>/image`. Mirrors stock-item / recipe pattern.
    has_image: bool
    is_active: bool
    is_available: bool
    store_id: UUID
    store_name: str
    # `merchant_stockcode` is the producer's SKU, kept
    # verbatim per the rename runbook.
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
        # `has_image` is stamped in bulk by `stamp_has_image` so we don't
        # trigger the deferred image-blob load per row (N+1).
        return ProductDto(
            brand = product.brand,
            has_image = False,
            is_active = product.is_active,
            is_available = product.is_available,
            store_id = product.store.id,
            store_name = product.store.name,
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
    "store_id": EntityField(Product, "_store_id"),
}


def stamp_has_image(repository, dtos: list[ProductDto]) -> None:
    """FU-014 — bulk-derive `has_image` from a single `image IS NOT NULL`
    pass that never touches the deferred image blob. Mirrors the
    stock-item / recipe pattern.
    """
    if not dtos:
        return
    product_ids = [p.product_id for p in dtos]
    product_table = db.metadata.tables["Product"]
    rows = repository.session.execute(
        select(product_table.c.id, product_table.c.image.isnot(None))
        .where(product_table.c.id.in_(product_ids))
    ).all()
    flag_by_id: dict[UUID, bool] = {row[0]: bool(row[1]) for row in rows}
    for dto in dtos:
        dto.has_image = flag_by_id.get(dto.product_id, False)


def stamp_linked_stock_items(repository, dtos: list[ProductDto]) -> None:
    """Stamp `linked_stock_item_*` on each DTO in place via the m2m join.

    One bulk query against the join, then a single StockItem lookup for the
    names. Shared by the products list and the best-deals query so the
    enrichment lives in one place.
    """
    if not dtos:
        return
    product_ids = [p.product_id for p in dtos]
    assoc = db.metadata.tables["StockItemProduct"]
    rows = repository.session.execute(
        select(assoc.c.product_id, assoc.c.stock_item_id)
        .where(assoc.c.product_id.in_(product_ids))
    ).all()
    product_to_stock: dict[UUID, UUID] = {row[0]: row[1] for row in rows}
    stock_ids = list({sid for sid in product_to_stock.values()})
    stock_lookup: dict[UUID, StockItem] = {}
    if stock_ids:
        items = repository.get(StockItem).all(
            EntityField(StockItem, "id").in_(stock_ids)
        )
        stock_lookup = {s.id: s for s in items}
    for dto in dtos:
        stock_id = product_to_stock.get(dto.product_id)
        if stock_id is None:
            continue
        dto.linked_stock_item_id = stock_id
        item = stock_lookup.get(stock_id)
        dto.linked_stock_item_name = item.name if item else None


class GetProductsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, options) -> Page[ProductDto]:
        page = (
            self.repository
            .get(Product)
            .include(Product.Fields.CURRENT_OFFER)
            .include(Product.Fields.STORE)
            .paginate(options, ProductDto.from_entity, field_map=_FIELD_MAP)
        )
        stamp_has_image(self.repository, page.items)
        stamp_linked_stock_items(self.repository, page.items)
        return page


class GetBestDealsHandler:
    """Top-N active products currently on special, ranked by discount %.

    State-ownership Type B (§8.2): the dashboard used to download *every*
    product and sort/slice in the browser. The server now owns the rank + slice
    and returns only the top N, using the one `discount_percent` rule (R-003).
    """
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, limit: int) -> list[ProductDto]:
        products = (
            self.repository
            .get(Product)
            .include(Product.Fields.CURRENT_OFFER)
            .include(Product.Fields.STORE)
            .all()
        )
        scored: list[tuple[int, Product]] = []
        for product in products:
            offer = product.current_offer
            if not product.is_active or offer is None:
                continue
            pct = discount_percent(offer.price_now, offer.price_was)
            if pct is None:
                continue
            scored.append((pct, product))
        # Highest discount first; matches the client's old discount-% sort.
        scored.sort(key=lambda t: t[0], reverse=True)
        dtos = [ProductDto.from_entity(p) for _, p in scored[:limit]]
        stamp_has_image(self.repository, dtos)
        stamp_linked_stock_items(self.repository, dtos)
        return dtos


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


@PRODUCT_ROUTER.route("/best-deals")
def get_best_deals():
    """Top-N on-special products by discount %. `?limit=N` (default 3, max 20)."""
    _Logger = logging.getLogger(__name__)
    _RawLimit = request.args.get("limit")
    _Limit = 3
    if _RawLimit is not None and _RawLimit.strip():
        try:
            _Limit = int(_RawLimit)
        except ValueError:
            return bad_request("`limit` must be an integer.")
    if _Limit < 1:
        return bad_request("`limit` must be at least 1.")
    _Limit = min(_Limit, 20)
    _Deals = get_container().inject(GetBestDealsHandler).handle(_Limit)
    _Logger.info(f"Retrieved {len(_Deals)} best deals (limit={_Limit}).")
    return ok(_Deals)
