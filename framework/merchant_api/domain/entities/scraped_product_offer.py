# TODO: Learn https://docs.pydantic.dev/2.3/usage/models/
# TODO: Learn https://docs.pydantic.dev/2.3/errors/errors/
import re
from dataclasses import dataclass, field


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
    size: str
    size_unit: str
    size_value: float
    web_url: str

    def __post_init__(self):
        self.price_difference = "{:.2f}".format(self.price_was - self.price_now)
        self.price_now = "{:.2f}".format(self.price_now)
        self.price_was = "{:.2f}".format(self.price_was)

    def get_size(size: str):
        # TODO: Instead make the unit the PK for the unit entity...ooooorrr...just don't worry about it and keep it as str
        # class SizeUnit(Enum):
        #     GRAM = 'g'
        #     KILOGRAM = 'kg'
        #     MILLILITER = 'ml'
        #     LITER = 'l'
        #     MILLIGRAM = 'mg'

        _SizePattern = r'(\d+(\.\d+)?)(\s*[a-zA-Z]+)'
        _Match = re.match(_SizePattern, size)

        if _Match:
            _Value = float(_Match.group(1))
            _Unit = str(_Match.group(3)).strip().upper()
            return _Value, _Unit

            # try:
            #     size_unit = SizeUnit[unit.lower()]
            # except KeyError:
            #     print(f"Invalid unit: {unit}")
            #     #TODO: LOG
            #     return None, None

        else:
            print(f"Unable to extract size from: {size}")
            #TODO: LOG
            return None, None
