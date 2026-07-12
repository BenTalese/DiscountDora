import logging
from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


@dataclass(slots=True)
class UnlinkProductResponse:
    stock_item_not_found: bool = False
    link_not_found: bool = False


class UnlinkProductFromStockItemHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, stock_item_id: UUID, product_id: UUID) -> UnlinkProductResponse:
        _StockItem = (
            self.repository
            .get(StockItem)
            .include(StockItem.Fields.PRODUCTS)
            .one(EntityField(StockItem, "id").eq(stock_item_id))
        )
        if not _StockItem:
            return UnlinkProductResponse(stock_item_not_found = True)

        # Find the linked product on the in-memory collection and remove it.
        # SQLAlchemy turns the removal into a DELETE on the m2m table.
        _Match = next((p for p in (_StockItem.products or []) if p.id == product_id), None)
        if _Match is None:
            return UnlinkProductResponse(link_not_found = True)

        _StockItem.products.remove(_Match)
        self.repository.save_changes()
        return UnlinkProductResponse()


@STOCK_ITEM_ROUTER.route("<uuid:stock_item_id>/products/<uuid:product_id>", methods=["DELETE"])
def unlink_product_from_stock_item(stock_item_id: UUID, product_id: UUID):
    _Logger = logging.getLogger(__name__)

    # Flask's default converter delivers path params as `str` despite the
    # annotation; the handler compares `p.id == product_id` in Python, so a
    # str here made the unlink 404 unconditionally (FU-528 str/UUID family).
    # Coerce at the HTTP boundary; malformed ids read as "link never existed".
    try:
        _ProductId = UUID(str(product_id))
    except ValueError:
        return not_found("StockItemProduct link", product_id)

    _Handler = UnlinkProductFromStockItemHandler(SqlAlchemyRepository())
    _Response = _Handler.handle(stock_item_id, _ProductId)

    if _Response.stock_item_not_found:
        return not_found(StockItem.__name__, stock_item_id)
    if _Response.link_not_found:
        # 204 is also reasonable for "no link to delete" but we surface 404
        # so a stale client can tell the difference between "link removed"
        # and "link never existed".
        return not_found("StockItemProduct link", product_id)

    _Logger.info("Unlinked product %s from stock item %s", product_id, stock_item_id)
    return no_content()
