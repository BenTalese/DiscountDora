from clapy import InputPort

from domain.entities.base_entity import EntityID

class DeleteStockLocationInputPort(InputPort):
    stock_location_id = EntityID
    