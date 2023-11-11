from dataclasses import dataclass
from typing import List
from domain.entities.base_entity import BaseEntity

from domain.entities.merchant import Merchant
from domain.entities.product_offer import ProductOffer


# # TODO PERHAPS THIS SHOULD JUST BE FLATTENED ON THE PRODUCT?
# @dataclass
# class Measurement(BaseEntity): # TODO: This should be owned in DB
#     quantity: int = None
#     unit: str = None

@dataclass
class Product(BaseEntity):
    brand: str = None
    current_offer: ProductOffer = None # flatten onto Product?
    # historical_offers: List[ProductOffer] = None
    image: str = None
    is_available: bool = None
    merchant: Merchant = None
    name: str = None
    size_unit: str = None
    size_value: str = None
    web_url: str = None
