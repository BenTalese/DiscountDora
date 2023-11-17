from abc import ABC, abstractmethod

from clapy import IOutputPort
from application.dtos.merchant_dto import MerchantDto

from application.services.iquerybuilder import IQueryBuilder


class IGetMerchantsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_merchants_async(self, merchants: IQueryBuilder[MerchantDto]) -> None:
        pass
