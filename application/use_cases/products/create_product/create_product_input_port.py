from clapy import InputPort

from domain.entities.base_entity import EntityID


class CreateProductInputPort(InputPort):
    brand: str = None
    price_now: float
    price_was: float
    image: bytes = None
    is_available: bool
    merchant_id: EntityID
    merchant_stockcode: str
    name: str
    size_unit: str
    size_value: float = 0 # TODO: Can be nothing?
    web_url: str
