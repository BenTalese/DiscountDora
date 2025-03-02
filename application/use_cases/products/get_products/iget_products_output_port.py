from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.services.iquerybuilder import IQueryBuilder
from domain.entities.product import Product


class IGetProductsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_products_async(self, products: IQueryBuilder[Product]) -> None:
        pass
