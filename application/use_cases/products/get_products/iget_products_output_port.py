from abc import ABC, abstractmethod

from clapy import IOutputPort
from application.dtos.product_dto import ProductDto

from application.services.iquerybuilder import IQueryBuilder


class IGetProductsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_products_async(self, products: IQueryBuilder[ProductDto]) -> None:
        pass
