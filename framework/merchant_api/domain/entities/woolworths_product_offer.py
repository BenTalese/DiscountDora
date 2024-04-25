from pydantic import BaseModel


class WoolworthsProductOffer(BaseModel, extra='allow'):
    Brand: str # 'Lindt'
    CupString: str # '$0.80 / 100G'
    IsAvailable: bool
    InstoreCupString: str
    InstoreIsAvailable: bool
    InstorePrice: float
    InstoreWasPrice: float
    LargeImageFile: str # 'https://cdn0.woolworths.media/content/wowproductimages/large/114682.jpg'
    Name: str # 'Lindt Lindor Milk Chocolate Balls'
    PackageSize: str # '333G'
    Price: float
    Stockcode: int
    WasPrice: float
