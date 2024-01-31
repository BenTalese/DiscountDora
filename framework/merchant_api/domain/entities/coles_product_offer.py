from typing import List, Optional
from pydantic import BaseModel


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
