from dataclasses import dataclass

from framework.merchant_api.models import ScrapedProductOffer


@dataclass
class ScrapedProductOfferViewModel:
    brand: str
    image: bytes
    is_available: bool
    # merchant_id: UUID # TODO
    merchant: str
    merchant_stockcode: str
    name: str
    price_now: float
    price_was: float
    size_unit: str
    size_value: float
    web_url: str

# TODO: Parameter should be a dto (perhaps it is a dto, just not named as one)
def get_scraped_product_offer_view_model(scraped_product_offer: ScrapedProductOffer) -> ScrapedProductOfferViewModel:
    return ScrapedProductOfferViewModel(
        brand = scraped_product_offer.brand,
        image = scraped_product_offer.image.decode('utf-8'), # TODO: Is this the correct place to do this?
        is_available = scraped_product_offer.is_available,
        merchant = scraped_product_offer.merchant,
        merchant_stockcode = scraped_product_offer.merchant_stockcode,
        name = scraped_product_offer.name,
        price_now = scraped_product_offer.price_now,
        price_was = scraped_product_offer.price_was,
        size_unit = scraped_product_offer.size_unit,
        size_value = scraped_product_offer.size_value,
        web_url = scraped_product_offer.web_url
    )
