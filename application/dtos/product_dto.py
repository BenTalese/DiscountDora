from dataclasses import dataclass
from typing import List
from application.dtos.product_offer_dto import ProductOfferDto, get_product_offer_dto

from domain.entities.base_entity import EntityID
from domain.entities.product import Product


@dataclass
class ProductDto:
    brand: str
    current_offer: ProductOfferDto
    historical_offers: List[ProductOfferDto]
    image: bytes
    is_available: bool
    merchant_id: EntityID
    merchant_stockcode: str
    name: str
    product_id: EntityID
    size_unit: str
    size_value: float
    web_url: str

def get_product_dto(product: Product) -> ProductDto:
    return ProductDto(
        brand = product.brand,
        current_offer = get_product_offer_dto(product.current_offer),
        historical_offers = [get_product_offer_dto(offer) for offer in product.historical_offers],
        image = product.image,
        is_available = product.is_available,
        merchant_id = product.merchant.id if product.merchant else None,
        merchant_stockcode = product.merchant_stockcode,
        name = product.name,
        product_id = product.id,
        size_unit = product.size_unit,
        size_value = product.size_value,
        web_url = product.web_url
    )
