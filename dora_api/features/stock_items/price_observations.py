"""Price-observation logging for a stock item (FU-213 / PROPOSAL_PRODUCTS_AS_OVERLAY §3.2).

The everyday "what this cost me" substrate: the user logs the TOTAL price + qty
+ unit; the per-unit cost is derived server-side. No merchant attribution here.
The money/spend feature gates the *surfaces* (the UI); the data itself is
harmless, so the endpoints aren't hard-gated — mirrors the products endpoints.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_item_price_observation import \
    StockItemPriceObservation
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class AddPriceObservationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price: float = Field(gt=0)
    qty: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=50)
    observed_at: datetime | None = None


@dataclass(slots=True)
class PriceObservationMutationResponse:
    stock_item_not_found: bool = False
    observation_not_found: bool = False


class PriceObservationHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def add(self, stock_item_id: UUID, request: AddPriceObservationRequest) -> PriceObservationMutationResponse:
        if not self.repository.get(StockItem).exists(stock_item_id):
            return PriceObservationMutationResponse(stock_item_not_found=True)
        self.repository.add(StockItemPriceObservation(
            stock_item_id=stock_item_id,
            price=float(request.price),
            qty=float(request.qty),
            unit=request.unit.strip(),
            observed_at=request.observed_at or datetime.now(timezone.utc),
            source="manual",
            created_at=datetime.now(timezone.utc),
        ))
        self.repository.save_changes()
        return PriceObservationMutationResponse()

    def delete(self, stock_item_id: UUID, observation_id: UUID) -> PriceObservationMutationResponse:
        match = self.repository.get(StockItemPriceObservation).one(
            EntityField(StockItemPriceObservation, "id").eq(observation_id)
            & EntityField(
                StockItemPriceObservation,
                StockItemPriceObservation.Fields.STOCK_ITEM_ID,
            ).eq(stock_item_id)
        )
        if match is None:
            return PriceObservationMutationResponse(observation_not_found=True)
        self.repository.remove(match)
        self.repository.save_changes()
        return PriceObservationMutationResponse()


@STOCK_ITEM_ROUTER.route("<stock_item_id>/price-observations", methods=["POST"])
@has_request_body(AddPriceObservationRequest)
def add_price_observation(stock_item_id: UUID):
    _Handler = get_container().inject(PriceObservationHandler)
    _Request: AddPriceObservationRequest = get_request_body()
    _Response = _Handler.add(stock_item_id, _Request)
    if _Response.stock_item_not_found:
        return not_found(StockItem.__name__, stock_item_id)
    logging.getLogger(__name__).info("Logged a price for stock item %s", stock_item_id)
    return no_content()


@STOCK_ITEM_ROUTER.route("<stock_item_id>/price-observations/<observation_id>", methods=["DELETE"])
def delete_price_observation(stock_item_id: UUID, observation_id: UUID):
    _Handler = get_container().inject(PriceObservationHandler)
    _Response = _Handler.delete(stock_item_id, observation_id)
    if _Response.observation_not_found:
        return not_found(StockItemPriceObservation.__name__, observation_id)
    return no_content()
