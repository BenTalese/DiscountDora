"""Price-history endpoint for a single product.

Powers the sparkline on the stock-item detail page. Returns the product's
historic offers plus its current offer as a single time-ordered series.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List
from uuid import UUID

from dora_api.domain.entities.product import Product
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


@dataclass(frozen=True, slots=True)
class PricePointDto:
    offered_on: datetime
    price_now: float | None
    price_was: float | None


@dataclass(frozen=True, slots=True)
class PriceHistoryDto:
    product_id: UUID
    points: List[PricePointDto]


class GetPriceHistoryHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, product_id: UUID) -> PriceHistoryDto | None:
        _Product: Product | None = (
            self.repository
            .get(Product)
            .include(Product.Fields.CURRENT_OFFER)
            .include(Product.Fields.HISTORIC_OFFERS)
            .one(EntityField(Product, "id").eq(product_id))
        )
        if not _Product:
            return None

        _Offers = list(_Product.historic_offers or [])
        if _Product.current_offer is not None:
            _Offers.append(_Product.current_offer)

        _Points = sorted(
            (
                PricePointDto(
                    offered_on = o.offered_on,
                    price_now = o.price_now,
                    price_was = o.price_was,
                )
                for o in _Offers
                if o.offered_on is not None
            ),
            key=lambda p: p.offered_on,
        )
        return PriceHistoryDto(product_id=product_id, points=_Points)


@PRODUCT_ROUTER.route("<uuid:product_id>/price-history")
def get_price_history(product_id: UUID):
    _Logger = logging.getLogger(__name__)
    _History = GetPriceHistoryHandler(SqlAlchemyRepository()).handle(product_id)
    if _History is None:
        return not_found(Product.__name__, product_id)
    _Logger.debug("Product %s price history: %d points", product_id, len(_History.points))
    return ok(_History)
