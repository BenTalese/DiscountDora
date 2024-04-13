from clapy import AttributeChangeTracker, InputPort

from domain.entities.base_entity import EntityID


class UpdateStockItemInputPort(InputPort):
    name: AttributeChangeTracker[str] = AttributeChangeTracker[str]()
    stock_item_id: EntityID
    stock_level_id: AttributeChangeTracker[EntityID] = AttributeChangeTracker[EntityID]()
    stock_location_id: AttributeChangeTracker[EntityID] = AttributeChangeTracker[EntityID]()
