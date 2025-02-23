from dataclasses import dataclass
from datetime import datetime
from domain.entities.base_entity import EntityID

from domain.entities.product_historic_offer import ProductHistoricOffer


@dataclass
class ProductHistoricOfferDto:
    offered_on: datetime
    price_now: float
    price_was: float
    product_historic_offer_id: EntityID


def get_product_historic_offer_dto(product_historic_offer: ProductHistoricOffer) -> ProductHistoricOfferDto:
    return ProductHistoricOfferDto(
        offered_on = product_historic_offer.offered_on,
        price_now = product_historic_offer.price_now,
        price_was = product_historic_offer.price_was,
        product_historic_offer_id = product_historic_offer.id
    )
