import datetime
from dataclasses import dataclass
from domain.entities.base_entity import EntityID

from domain.entities.product_offer import ProductOffer


@dataclass
class ProductOfferDto:
    id: EntityID
    offered_on: datetime
    price_now: float
    price_was: float

def get_product_offer_dto(product_offer: ProductOffer) -> ProductOfferDto:
    return ProductOfferDto(
        id = product_offer.id,
        offered_on = product_offer.offered_on,
        price_now = product_offer.price_now,
        price_was = product_offer.price_was
    )
