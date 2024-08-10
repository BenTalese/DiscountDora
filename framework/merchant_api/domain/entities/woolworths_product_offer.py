from pydantic import BaseModel


class WoolworthsProductOffer(BaseModel, extra='allow'):
    Brand: str
    CupString: str  # '$0.80 / 100G'
    IsAvailable: bool
    InstoreCupString: str
    InstoreIsAvailable: bool
    InstorePrice: float
    InstoreWasPrice: float
    LargeImageFile: str
    Name: str
    PackageSize: str  # '333G'
    Price: float
    Stockcode: int
    WasPrice: float
