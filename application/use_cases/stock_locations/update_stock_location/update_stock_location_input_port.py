from clapy import InputPort

from application.infrastructure.attribute_change_tracker import \
    AttributeChangeTracker
from domain.entities.base_entity import EntityID

class UpdateStockLocationInputPort(InputPort):
    description: AttributeChangeTracker[str] = AttributeChangeTracker[str]
    stock_location_id: EntityID
