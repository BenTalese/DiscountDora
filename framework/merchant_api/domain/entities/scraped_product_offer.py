import logging
import re
from dataclasses import dataclass, field


@dataclass
class ScrapedProductOffer:
    brand: str
    image_uri: str
    image: str | None
    is_available: bool
    merchant_name: str
    merchant_stockcode: str
    name: str
    price_difference: float = field(init=False)
    price_now: float
    price_per_cup: str | None
    price_was: float
    size_unit: str | None
    size_value: float | None
    size: str
    web_url: str

    def __post_init__(self):
        self.price_difference = "{:.2f}".format(self.price_was - self.price_now)
        self.price_now = "{:.2f}".format(self.price_now)
        self.price_was = "{:.2f}".format(self.price_was)

    def _extract_value_and_unit_from_size(size: str):
        _SizePattern = r'(\d+(\.\d+)?)(\s*[a-zA-Z]+)'
        _Match = re.match(_SizePattern, size)

        if _Match:
            _Value = float(_Match.group(1))
            _Unit = str(_Match.group(3)).strip().upper()
            return _Value, _Unit

        else:
            logging.getLogger(__name__).warning(f"Unable to extract value and unit from size {size}.")
            return None, None
