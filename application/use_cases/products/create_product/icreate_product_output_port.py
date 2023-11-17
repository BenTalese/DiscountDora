from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.dtos.product_dto import ProductDto
from domain.entities.base_entity import EntityID


class ICreateProductOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_merchant_not_found_async(self, merchant_id: EntityID) -> None:
        pass

    @abstractmethod
    async def present_product_created_async(self, product: ProductDto) -> None:
        pass
