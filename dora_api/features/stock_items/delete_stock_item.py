from dataclasses import dataclass
import logging
from uuid import UUID

from varname import nameof

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True)
class DeleteStockItemResponse:
    stock_item_not_found: bool = False


class DeleteStockItemHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, stock_item_id: EntityID) -> DeleteStockItemResponse:
        _StockItem = self.repository.get(StockItem).by_id(stock_item_id)

        if not _StockItem:
            return DeleteStockItemResponse(stock_item_not_found = True)

        self.repository.remove(_StockItem)
        self.repository.save_changes()

        return DeleteStockItemResponse()


@STOCK_ITEM_ROUTER.route("<stock_item_id>", methods=["DELETE"])
def delete_stock_item(stock_item_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to delete stock item.")
    _Handler: DeleteStockItemHandler = get_container().inject(DeleteStockItemHandler)
    _Response = _Handler.handle(EntityID(stock_item_id))

    if _Response.stock_item_not_found:
        _Logger.warning(f"Stock item not found with ID: {stock_item_id}")
        return not_found(nameof(StockItem), stock_item_id)

    _Logger.info(f"Successfully deleted stock item with ID {stock_item_id}.")
    return no_content()
