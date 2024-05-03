from clapy import AttributeChangeTracker, InputPort

from domain.entities.base_entity import EntityID


class UpdateProductInputPort(InputPort):
    is_active: AttributeChangeTracker[bool] = AttributeChangeTracker[bool]()
    is_available: AttributeChangeTracker[bool] = AttributeChangeTracker[bool]()
    price_now: AttributeChangeTracker[float] = AttributeChangeTracker[float]()
    price_was: AttributeChangeTracker[float] = AttributeChangeTracker[float]()
    product_id: EntityID
