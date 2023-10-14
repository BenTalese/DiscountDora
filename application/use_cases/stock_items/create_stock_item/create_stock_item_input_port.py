from clapy import InputPort

from domain.entities.base_entity import EntityID


class CreateStockItemInputPort(InputPort):
    location_id: EntityID = None
    name: str
    stock_level_id: EntityID = None
