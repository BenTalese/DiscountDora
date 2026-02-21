from dataclasses import dataclass
from uuid import UUID

from varname import nameof

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.infrastructure.utils import get_container
from dora_api.services.irepository import IRepository


@dataclass(slots=True)
class DeleteStockItemResponse:
    stock_item_not_found: bool = False


class DeleteStockItemHandler:
    def __init__(self, stock_item_repository: IRepository[StockItem]):
        self.stock_item_repository = stock_item_repository

    def handle(self, stock_item_id: EntityID) -> DeleteStockItemResponse:
        _StockItem = self.stock_item_repository.get().by_id(stock_item_id)

        if not _StockItem:
            return DeleteStockItemResponse(stock_item_not_found = True)

        self.stock_item_repository.remove(_StockItem)
        self.stock_item_repository.save_changes()

        return DeleteStockItemResponse()


@STOCK_ITEM_ROUTER.route("<stock_item_id>", methods=["DELETE"])
def delete_stock_item(stock_item_id: UUID):
    _Handler: DeleteStockItemHandler = get_container().inject(DeleteStockItemHandler)
    _Response = _Handler.handle(EntityID(stock_item_id))

    if _Response.stock_item_not_found:
        return not_found(nameof(StockItem), stock_item_id)

    return no_content()
