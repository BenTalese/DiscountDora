import logging
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  entity_existence_failure,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class AddSubstituteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    substitute_id: UUID


@dataclass(slots=True)
class AddSubstituteResponse:
    stock_item_not_found: bool = False
    substitute_not_found: bool = False
    is_self: bool = False
    already_linked: bool = False


class AddSubstituteHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, stock_item_id: UUID, request: AddSubstituteRequest) -> AddSubstituteResponse:
        if str(stock_item_id) == str(request.substitute_id):
            return AddSubstituteResponse(is_self=True)

        if not self.repository.get(StockItem).exists(stock_item_id):
            return AddSubstituteResponse(stock_item_not_found=True)
        if not self.repository.get(StockItem).exists(request.substitute_id):
            return AddSubstituteResponse(substitute_not_found=True)

        # Directed self-referential m2m operated on directly — the generic
        # repository can't self-join StockItem. Idempotent: a duplicate (PK
        # collision) is reported as already-linked rather than an error.
        _Assoc = db.metadata.tables["StockItemSubstitute"]
        _Existing = db.session.execute(
            select(_Assoc.c.substitute_id).where(
                (_Assoc.c.stock_item_id == stock_item_id)
                & (_Assoc.c.substitute_id == request.substitute_id)
            )
        ).first()
        if _Existing is not None:
            return AddSubstituteResponse(already_linked=True)

        db.session.execute(
            _Assoc.insert().values(
                stock_item_id=stock_item_id, substitute_id=request.substitute_id
            )
        )
        self.repository.save_changes()
        return AddSubstituteResponse()


@STOCK_ITEM_ROUTER.route("<stock_item_id>/substitutes", methods=["POST"])
@has_request_body(AddSubstituteRequest)
def add_substitute(stock_item_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(AddSubstituteHandler)
    _Request: AddSubstituteRequest = get_request_body()
    _Response = _Handler.handle(stock_item_id, _Request)

    if _Response.stock_item_not_found:
        return not_found(StockItem.__name__, stock_item_id)
    if _Response.is_self:
        return business_rule_violation("A stock item can't be its own substitute.")
    if _Response.substitute_not_found:
        return entity_existence_failure(
            StockItem.__name__,
            field_of(AddSubstituteRequest, "substitute_id"),
            _Request.substitute_id,
        )

    _Logger.info(
        "Added substitute %s to stock item %s%s",
        _Request.substitute_id,
        stock_item_id,
        " (already linked)" if _Response.already_linked else "",
    )
    return no_content()
