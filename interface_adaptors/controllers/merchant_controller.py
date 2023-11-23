from typing import List

from clapy import PipeConfiguration

from application.use_cases.merchants.get_merchants.get_merchants_input_port import \
    GetMerchantsInputPort
from application.use_cases.merchants.get_merchants.iget_merchants_output_port import \
    IGetMerchantsOutputPort

from .base_controller import DEFAULT_PIPELINE, BaseController


class MerchantController(BaseController):

    async def get_merchants_async(
            self,
            output_port: IGetMerchantsOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        await self._use_case_invoker.invoke_usecase_async(GetMerchantsInputPort(), output_port, pipeline_configuration)
