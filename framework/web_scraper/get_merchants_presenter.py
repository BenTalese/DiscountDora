from typing import List
from application.dtos.merchant_dto import MerchantDto
from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.merchants.get_merchants.iget_merchants_output_port import IGetMerchantsOutputPort


class GetMerchantsPresenter(IGetMerchantsOutputPort):
    merchants: List[MerchantDto] = None

    async def present_merchants_async(self, merchants: IQueryBuilder[MerchantDto]):
        self.merchants = merchants.execute()
