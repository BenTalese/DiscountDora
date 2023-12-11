from clapy import InputPort

from application.infrastructure.attribute_change_tracker import \
    AttributeChangeTracker
from domain.entities.base_entity import EntityID


# BUG: Clapy InputTypeValidator needs to do "type(type_hint)" to work with AttributeChangeTracker
class UpdateProductInputPort(InputPort):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    is_available: AttributeChangeTracker[bool] = AttributeChangeTracker[bool]()
    price_now: AttributeChangeTracker[float] = AttributeChangeTracker[float]()
    price_was: AttributeChangeTracker[float] = AttributeChangeTracker[float]()
    product_id: EntityID
