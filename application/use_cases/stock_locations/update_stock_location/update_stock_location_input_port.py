from clapy import AttributeChangeTracker, InputPort

from domain.entities.base_entity import EntityID


class UpdateStockLocationInputPort(InputPort):
    description: AttributeChangeTracker[str] = AttributeChangeTracker[str]()
    stock_location_id: EntityID
