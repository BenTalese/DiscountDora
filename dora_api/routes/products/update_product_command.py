from dataclasses import dataclass

from clapy import AttributeChangeTracker


@dataclass
class UpdateProductCommand():
    is_active: AttributeChangeTracker[bool] = AttributeChangeTracker[bool]()
    is_available: AttributeChangeTracker[bool] = AttributeChangeTracker[bool]()
    price_now: AttributeChangeTracker[float] = AttributeChangeTracker[float]()
    price_was: AttributeChangeTracker[float] = AttributeChangeTracker[float]()
