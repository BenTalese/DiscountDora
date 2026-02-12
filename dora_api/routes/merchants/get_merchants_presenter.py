from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.merchants.get_merchants.iget_merchants_output_port import \
    IGetMerchantsOutputPort
from domain.entities.merchant import Merchant
from framework.dora_api.infrastructure.base_presenter import BasePresenter
from framework.dora_api.view_models.merchant_view_model import \
    get_merchant_view_model


class GetMerchantsPresenter(BasePresenter, IGetMerchantsOutputPort):
    async def present_merchants_async(self, merchants: IQueryBuilder[Merchant]):
        await self.ok_async(merchants.project(get_merchant_view_model).execute())
