from pydantic import BaseModel


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
