from typing import Optional

from pydantic import BaseModel


class IGAProductOffer(BaseModel, extra='allow'):
    class Size(BaseModel, extra='allow'):
        abbreviation: str
        size: float

    available: bool
    brand: str
    image: dict[str, Optional[str]] = None
    name: str
    price: str
    priceNumeric: float
    pricePerUnit: Optional[str] = None  # "$0.64/100ml"
    productId: str
    unitOfSize: Size
    wasPrice: Optional[str] = None
    wasPriceNumeric: Optional[float] = None
    wasWholePrice: Optional[float] = None
    wholePrice: float
