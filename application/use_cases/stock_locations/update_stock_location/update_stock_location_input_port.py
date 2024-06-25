from clapy import AttributeChangeTracker, InputPort

from domain.entities.base_entity import EntityID


class UpdateStockLocationInputPort(InputPort):
    name: AttributeChangeTracker[str] = AttributeChangeTracker[str]()
    stock_location_id: EntityID
