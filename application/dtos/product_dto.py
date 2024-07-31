from dataclasses import dataclass
from typing import List
from application.dtos.merchant_dto import MerchantDto, get_merchant_dto
from application.dtos.product_offer_dto import ProductOfferDto, get_product_offer_dto

from domain.entities.base_entity import EntityID
from domain.entities.product import Product


@dataclass
class ProductDto:
    brand: str
    current_offer: ProductOfferDto
    historical_offers: List[ProductOfferDto]
    image: bytes
    is_active: bool
    is_available: bool
    merchant: MerchantDto
    merchant_stockcode: str
    name: str
    product_id: EntityID
    size: str
    size_unit: str
    size_value: float
    web_url: str

def get_product_dto(product: Product) -> ProductDto:
    return ProductDto(
        brand = product.brand,
        # HACK: Added if condition for current_offer, due to issues with
        # .ThenInclude not loading the current_offer in the get stock items interactor
        current_offer = get_product_offer_dto(product.current_offer) if product.current_offer else None,
        historical_offers = [get_product_offer_dto(offer) for offer in product.historical_offers],
        image = product.image,
        is_active = product.is_active,
        is_available = product.is_available,
        merchant = get_merchant_dto(product.merchant) if product.merchant else None,
        merchant_stockcode = product.merchant_stockcode,
        name = product.name,
        product_id = product.id,
        size = product.size,
        size_unit = product.size_unit,
        size_value = product.size_value,
        web_url = product.web_url
    )
