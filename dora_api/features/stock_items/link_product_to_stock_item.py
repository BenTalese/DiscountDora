import logging
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import (entity_existence_failure,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class LinkProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID


@dataclass(slots=True)
class LinkProductResponse:
    stock_item_not_found: bool = False
    product_not_found: bool = False
    already_linked: bool = False


class LinkProductToStockItemHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, stock_item_id: UUID, request: LinkProductRequest) -> LinkProductResponse:
        _StockItem = (
            self.repository
            .get(StockItem)
            .include(StockItem.Fields.PRODUCTS)
            .one(EntityField(StockItem, "id").eq(stock_item_id))
        )
        if not _StockItem:
            return LinkProductResponse(stock_item_not_found = True)

        _Product = self.repository.get(Product).by_id(request.product_id)
        if not _Product:
            return LinkProductResponse(product_not_found = True)

        # Idempotent: re-linking is a no-op rather than an error. Lets the
        # frontend retry without worrying about double-link errors.
        existing_ids = {p.id for p in (_StockItem.products or [])}
        if _Product.id in existing_ids:
            return LinkProductResponse(already_linked = True)

        _StockItem.products.append(_Product)
        self.repository.save_changes()
        return LinkProductResponse()


@STOCK_ITEM_ROUTER.route("<stock_item_id>/products", methods=["POST"])
@has_request_body(LinkProductRequest)
def link_product_to_stock_item(stock_item_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(LinkProductToStockItemHandler)
    _Request: LinkProductRequest = get_request_body()
    _Response = _Handler.handle(stock_item_id, _Request)

    if _Response.stock_item_not_found:
        return not_found(StockItem.__name__, stock_item_id)
    if _Response.product_not_found:
        return entity_existence_failure(
            Product.__name__,
            field_of(LinkProductRequest, 'product_id'),
            _Request.product_id,
        )

    _Logger.info(
        "Linked product %s to stock item %s%s",
        _Request.product_id,
        stock_item_id,
        " (already linked)" if _Response.already_linked else "",
    )
    return no_content()
