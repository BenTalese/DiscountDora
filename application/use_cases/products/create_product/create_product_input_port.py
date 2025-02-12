from clapy import InputPort


class CreateProductInputPort(InputPort):
    brand: str = None
    image: bytes = None
    is_active: bool
    is_available: bool
    merchant_name: str
    merchant_stockcode: str
    name: str
    price_now: float
    price_was: float
    size: str
    size_unit: str
    size_value: float = 0  # TODO: Can be nothing?
    web_url: str
