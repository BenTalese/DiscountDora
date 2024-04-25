# TODO: Learn https://docs.pydantic.dev/2.3/usage/models/
# TODO: Learn https://docs.pydantic.dev/2.3/errors/errors/
import re
from dataclasses import dataclass, field

from framework.merchant_api.domain.entities.coles_product_offer import \
    ColesProductOffer
from framework.merchant_api.domain.entities.woolworths_product_offer import \
    WoolworthsProductOffer
from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant


# TODO: Possibly want price_was to be nullable (appears as 0 sometimes...)
# TODO: Remove image from here, and put image on dto instead of image_uri
@dataclass
class ScrapedProductOffer:
    brand: str
    image: bytes
    image_uri: str
    is_available: bool
    merchant_name: str
    merchant_stockcode: str
    name: str
    price_difference: float = field(init=False)
    price_now: float
    price_per_cup: str | None
    price_was: float
    size : str = field(init=False)
    size_unit: str
    size_value: float
    web_url: str

    # TODO LOOk if can do in method before translates
    def __post_init__(self):
        self.name = self.name if self.brand in self.name else f"{self.brand} {self.name}"
        self.price_difference = "{:.2f}".format(self.price_was - self.price_now)
        self.price_now = "{:.2f}".format(self.price_now)
        self.price_was = "{:.2f}".format(self.price_was)
        self.size = f"{self.size_value}{self.size_unit}" if self.size_value else self.size_unit

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
            unit = str(_Match.group(3)).upper()

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
            brand = offer.Brand or '',
            image = None,
            image_uri = offer.LargeImageFile,
            is_available = offer.IsAvailable or offer.InstoreIsAvailable,
            merchant_name = SupportedMerchant.WOOLWORTHS.value,
            merchant_stockcode = offer.Stockcode,
            name = offer.Name,
            price_now = offer.Price or offer.InstorePrice or 0,
            price_per_cup = (offer.CupString.upper() if offer.CupString else None)
                or (offer.InstoreCupString.upper() if offer.InstoreCupString else None),
            price_was = offer.WasPrice or offer.InstoreWasPrice or 0,
            size_unit = _Unit or offer.PackageSize.upper(),
            size_value = _Value,
            web_url = f"https://www.woolworths.com.au/shop/productdetails/{offer.Stockcode}"
        )

    def translate_coles_offer(offer: ColesProductOffer) -> 'ScrapedProductOffer':
        _Value, _Unit = ScrapedProductOffer.get_size(offer.size)

        return ScrapedProductOffer(
            brand = offer.brand or '',
            image = None,
            image_uri = f"https://productimages.coles.com.au/productimages{offer.imageUris[0].uri}",
            is_available = offer.availability,
            merchant_name = SupportedMerchant.COLES.value,
            merchant_stockcode = offer.id,
            name = offer.name,
            price_now = offer.pricing.now if offer.pricing else 0,
            price_per_cup = offer.pricing.comparable.upper() if offer.pricing else None,
            price_was = offer.pricing.was if offer.pricing else 0,
            size_unit = _Unit or offer.size.upper(),
            size_value = _Value,
            web_url = f"https://www.coles.com.au/product/{offer.id}"
        )
