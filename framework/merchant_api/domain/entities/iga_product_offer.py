from typing import Any, Optional
from pydantic import BaseModel


class IgaProductOffer(BaseModel, extra='allow'):
    class Size(BaseModel, extra='allow'):
        abbreviation: str  # "ml"
        label: str  # "Millilitre"
        size: int  # 500
        type: str  # "millilitre"

    # attributes: ...
    available: bool
    barcode: str
    brand: str
    # categories: ...
    # defaultCategory: ...
    description: str
    image: dict[str, Optional[str]] = None # TODO: How do images work here?
    isFavorite: bool
    isPastPurchased: bool
    name: str
    price: str  # "$3.20" n.b. omitted due to clash with class-property
    priceLabel: str
    priceNumeric: float  # 3.2
    pricePerUnit: Optional[str] = None  # "$0.64/100ml"
    priceSource: str
    productId: str
    sellBy: str
    sku: str
    # tprPrice: ...
    # unitOfMeasure: ...
    # unitOfPrice: ...
    unitOfSize: Size
    wasPrice: Optional[str] = None
    wasPriceNumeric: Optional[float] = None
    wasWholePrice: Optional[float] = None
    weightIncrement: Any # TODO: ?
    wholePrice: float
