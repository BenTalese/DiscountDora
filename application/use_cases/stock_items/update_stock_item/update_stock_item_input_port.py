from clapy import AttributeChangeTracker, InputPort
from typing import List

from domain.entities.base_entity import EntityID


class UpdateStockItemInputPort(InputPort):
    name: AttributeChangeTracker[str] = AttributeChangeTracker[str]()
    product_ids_to_add: AttributeChangeTracker[List[EntityID] | None] = AttributeChangeTracker[List[EntityID]]()
    product_ids_to_remove: AttributeChangeTracker[List[EntityID] | None] = AttributeChangeTracker[List[EntityID]]()
    stock_item_id: EntityID
    stock_level_id: AttributeChangeTracker[EntityID] = AttributeChangeTracker[EntityID]()
    stock_location_id: AttributeChangeTracker[EntityID] = AttributeChangeTracker[EntityID]()
