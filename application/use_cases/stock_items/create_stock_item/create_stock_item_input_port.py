from clapy import InputPort

from domain.entities.base_entity import EntityID


class CreateStockItemInputPort(InputPort):
    name: str
    stock_level_id: EntityID
    stock_location_id: EntityID = None
