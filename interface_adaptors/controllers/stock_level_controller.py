from typing import List

from clapy import PipeConfiguration

from application.use_cases.stock_levels.get_stock_levels.get_stock_levels_input_port import \
    GetStockLevelsInputPort
from application.use_cases.stock_levels.get_stock_levels.iget_stock_levels_output_port import \
    IGetStockLevelsOutputPort

from .base_controller import DEFAULT_PIPELINE, BaseController


class StockLevelController(BaseController):

    async def get_stock_levels_async(
            self,
            output_port: IGetStockLevelsOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        await self._use_case_invoker.invoke_usecase_async(GetStockLevelsInputPort(), output_port, pipeline_configuration)
