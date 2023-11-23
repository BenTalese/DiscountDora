from application.dtos.merchant_dto import MerchantDto
from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.merchants.get_merchants.iget_merchants_output_port import \
    IGetMerchantsOutputPort
from framework.api.base_presenter import BasePresenter
from framework.api.view_models.merchant_view_model import \
    get_merchant_view_model


class GetMerchantsPresenter(BasePresenter, IGetMerchantsOutputPort):
    async def present_merchants_async(self, merchants: IQueryBuilder[MerchantDto]):
        await self.ok_async(merchants.project(get_merchant_view_model).execute())
