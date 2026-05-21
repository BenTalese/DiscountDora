import logging
from dataclasses import dataclass
from uuid import UUID

from dora_api.app import db
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True)
class RemoveSubstituteResponse:
    stock_item_not_found: bool = False
    link_not_found: bool = False


class RemoveSubstituteHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, stock_item_id: UUID, substitute_id: UUID) -> RemoveSubstituteResponse:
        if not self.repository.get(StockItem).exists(stock_item_id):
            return RemoveSubstituteResponse(stock_item_not_found=True)

        _Assoc = db.metadata.tables["StockItemSubstitute"]
        _Result = db.session.execute(
            _Assoc.delete().where(
                (_Assoc.c.stock_item_id == stock_item_id)
                & (_Assoc.c.substitute_id == substitute_id)
            )
        )
        if _Result.rowcount == 0:
            return RemoveSubstituteResponse(link_not_found=True)

        self.repository.save_changes()
        return RemoveSubstituteResponse()


@STOCK_ITEM_ROUTER.route("<stock_item_id>/substitutes/<substitute_id>", methods=["DELETE"])
def remove_substitute(stock_item_id: UUID, substitute_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(RemoveSubstituteHandler)
    _Response = _Handler.handle(stock_item_id, substitute_id)

    if _Response.stock_item_not_found:
        return not_found(StockItem.__name__, stock_item_id)
    if _Response.link_not_found:
        return not_found("StockItemSubstitute link", substitute_id)

    _Logger.info("Removed substitute %s from stock item %s", substitute_id, stock_item_id)
    return no_content()
