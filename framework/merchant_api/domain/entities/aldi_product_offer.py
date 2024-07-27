from pydantic import BaseModel


class AldiProductOffer(BaseModel, extra='allow'):
    amount: str
    current_price_decimal: str
    current_price_value: str
    description: str
    former_price: str
    image_uri: str
    product_url: str
    unit_price: str
