from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.services.iquerybuilder import IQueryBuilder
from domain.entities.merchant import Merchant


class IGetMerchantsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_merchants_async(self, merchants: IQueryBuilder[Merchant]) -> None:
        pass
