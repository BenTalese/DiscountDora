from clapy import InputPort

from application.infrastructure.attribute_change_tracker import \
    AttributeChangeTracker
from domain.entities.base_entity import EntityID

class UpdateStockLocationInputPort(InputPort):
    description = AttributeChangeTracker[str] = AttributeChangeTracker[str] #How restrictive do we want to be? Can they provide nothing?
    stock_location_id = EntityID

#Do we want validation against description? not empty / empty str