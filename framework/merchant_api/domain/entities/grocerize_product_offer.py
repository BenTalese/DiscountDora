from typing import List, Optional
from pydantic import BaseModel


class GrocerizeProductOffer(BaseModel, extra='allow'):
    class VendorOfferInfo(BaseModel, extra='allow'):
        available: bool
        cup_price: Optional[float]
        cup_volume: Optional[str]
        price: float
        special_original_price: Optional[float]
        vendor_id: int
        vendor_product_code: int
        volume: str

    image_url: str
    item_pricing: List[VendorOfferInfo]
    name: str
