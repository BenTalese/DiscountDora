# TODO: Learn https://docs.pydantic.dev/2.3/usage/models/
# TODO: Learn https://docs.pydantic.dev/2.3/errors/errors/
import base64
from dataclasses import dataclass
from enum import Enum
import re
from typing import List, Optional, Tuple

from pydantic import BaseModel
import requests


class WoolworthsProductOffer(BaseModel, extra='allow'):
    Brand: str # 'Lindt'
    Stockcode: int
    IsAvailable: bool
    InstoreIsAvailable: bool
    Name: str # 'Lindt Lindor Milk Chocolate Balls'
    Price: float
    InstorePrice: float
    WasPrice: float
    InstoreWasPrice: float
    LargeImageFile: str # 'https://cdn0.woolworths.media/content/wowproductimages/large/114682.jpg'
    PackageSize: str # '333G'

class ColesProductOffer(BaseModel, extra='allow'):
    class ImageInfo(BaseModel, extra='allow'):
        uri: str

    class Pricing(BaseModel, extra='allow'):
        now: float
        was: float

    imageUris: List[ImageInfo]
    id: int
    name: str
    brand: str
    size: str # "352g"
    availability: bool
    pricing: Optional[Pricing] # None if `availability=False`

@dataclass
class ScrapedProductOffer:
    # id: int #possibly irrelevant, might just want url/link
    brand: str
    image: str
    image_uri: str
    is_available: bool
    merchant: str # TODO: hmm...str? or id of merchant? would have to use GetMerchants or create if not found
    name: str
    price_now: float
    price_was: float
    size_unit: str
    size_value: float
    web_url: str

    def get_size(size: str):
        # TODO: Instead make the unit the PK for the unit entity...ooooorrr...just don't worry about it and keep it as str
        # class SizeUnit(Enum):
        #     GRAM = 'g'
        #     KILOGRAM = 'kg'
        #     MILLILITER = 'ml'
        #     LITER = 'l'
        #     MILLIGRAM = 'mg'

        _SizePattern = r'(\d+)(\.\d+)?([a-zA-Z]+)'
        _Match = re.match(_SizePattern, size)

        if _Match:
            value = float(_Match.group(1))
            unit = str(_Match.group(3)).lower()

            # try:
            #     size_unit = SizeUnit[unit.lower()]
            # except KeyError:
            #     print(f"Invalid unit: {unit}")
            #     #TODO: LOG
            #     return None, None

            return value, unit

        else:
            print(f"Unable to extract size from: {size}")
            #TODO: LOG
            return None, None

    def translate_woolworths_offer(offer: WoolworthsProductOffer) -> 'ScrapedProductOffer':
        _Value, _Unit = ScrapedProductOffer.get_size(offer.PackageSize)

        return ScrapedProductOffer(
            brand = offer.Brand,
            # id = offer.Stockcode,
            image = None,
            image_uri = offer.LargeImageFile,
            is_available = offer.IsAvailable or offer.InstoreIsAvailable,
            merchant = "Woolworths",
            name = offer.Name,
            price_now = offer.Price or offer.InstorePrice,
            price_was = offer.WasPrice or offer.InstoreWasPrice,
            size_unit = _Unit or offer.PackageSize,
            size_value = _Value,
            web_url = f"https://www.woolworths.com.au/shop/productdetails/{offer.Stockcode}"
        )

    def translate_coles_offer(offer: ColesProductOffer) -> 'ScrapedProductOffer':
        _Value, _Unit = ScrapedProductOffer.get_size(offer.size)

        return ScrapedProductOffer(
            brand = offer.brand,
            # id = offer.id,
            image = None,
            image_uri = f"https://productimages.coles.com.au/productimages{offer.imageUris[0].uri}",
            is_available = offer.availability,
            merchant = "Coles",
            name = offer.name,
            price_now = offer.pricing.now if offer.pricing else None,
            price_was = offer.pricing.was if offer.pricing else None,
            size_unit = _Unit or offer.size,
            size_value = _Value,
            web_url = f"https://www.coles.com.au/product/{offer.id}"
        )
