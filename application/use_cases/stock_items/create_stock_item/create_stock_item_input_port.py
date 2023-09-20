import uuid

from clapy import InputPort


class CreateStockItemInputPort(InputPort):
    location_id: uuid = None
    name: str
    stock_level_id: uuid = None
