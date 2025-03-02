from abc import ABC, abstractmethod

from clapy import IOutputPort, IValidationOutputPort

from domain.entities.base_entity import EntityID
from domain.entities.product import Product


class IUpdateProductOutputPort(IOutputPort, IValidationOutputPort, ABC):

    @abstractmethod
    async def present_product_not_found_async(self, product_id: EntityID) -> None:
        pass

    @abstractmethod
    async def present_product_updated_async(self, product: Product) -> None:
        pass
