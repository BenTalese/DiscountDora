from abc import ABC, abstractmethod

from clapy import IOutputPort, IValidationOutputPort
from application.dtos.product_dto import ProductDto

from domain.entities.base_entity import EntityID


class IUpdateProductOutputPort(IOutputPort, IValidationOutputPort, ABC):

    @abstractmethod
    async def present_product_not_found_async(self, product_id: EntityID) -> None:
        pass

    @abstractmethod
    async def present_product_updated_async(self, product: ProductDto) -> None:
        pass
