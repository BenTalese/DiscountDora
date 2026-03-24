from pydantic import BaseModel


class SaveOnGroceriesProductOffer(BaseModel, extra='allow'):
    name: str
    price: float
    product_image_url: str
    product_package_size: str
    product_price_per_amount: str
    product_price_saving: float
    product_url: str
