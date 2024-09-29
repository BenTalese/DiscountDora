from dataclasses import dataclass
from datetime import datetime
from domain.entities.base_entity import EntityID

from domain.entities.product_offer import ProductOffer


@dataclass
class ProductOfferDto:
    offered_on: datetime
    price_difference: float
    price_now: float
    price_per_cup: str
    price_was: float
    product_offer_id: EntityID

def get_product_offer_dto(product_offer: ProductOffer) -> ProductOfferDto:
    return ProductOfferDto(
        offered_on = product_offer.offered_on,
        price_difference = product_offer.price_difference,
        price_now = product_offer.price_now,
        price_per_cup = product_offer.price_per_cup,
        price_was = product_offer.price_was,
        product_offer_id = product_offer.id
    )
