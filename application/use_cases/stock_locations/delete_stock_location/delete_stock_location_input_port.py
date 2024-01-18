from clapy import InputPort

from domain.entities.base_entity import EntityID

#is accessibility a thing for these classes?
class DeleteStockLocationInputPort(InputPort):
    stock_location_id = EntityID
    