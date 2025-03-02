from abc import ABC, abstractmethod

from clapy import IOutputPort, IValidationOutputPort

from domain.entities.base_entity import EntityID
from domain.entities.product import Product


class ICreateProductOutputPort(IOutputPort, IValidationOutputPort, ABC):

    @abstractmethod
    async def present_merchant_not_found_async(self, merchant_id: EntityID) -> None:
        pass

    @abstractmethod
    async def present_product_already_exists_async(self) -> None:
        pass

    @abstractmethod
    async def present_product_created_async(self, product: Product) -> None:
        pass
