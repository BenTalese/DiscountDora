from typing import List, Optional
from pydantic import BaseModel


class ColesProductOffer(BaseModel, extra='allow'):
    class ImageInfo(BaseModel, extra='allow'):
        uri: str

    class Pricing(BaseModel, extra='allow'):
        comparable: str  # '$0.54 per 1ea'
        now: float
        was: float

    availability: bool
    brand: str
    id: int
    imageUris: List[ImageInfo]
    name: str
    pricing: Optional[Pricing]  # None if `availability=False`
    size: str  # "352g"
