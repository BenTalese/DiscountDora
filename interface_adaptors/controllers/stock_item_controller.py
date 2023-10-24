from typing import List

from clapy import PipeConfiguration

from application.use_cases.stock_items.get_stock_items.get_stock_items_input_port import \
    GetStockItemsInputPort
from application.use_cases.stock_items.get_stock_items.iget_stock_items_output_port import \
    IGetStockItemsOutputPort

from .base_controller import DEFAULT_PIPELINE, BaseController


class StockItemController(BaseController):

    async def get_stock_items_async(
            self,
            output_port: IGetStockItemsOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        await self._use_case_invoker.invoke_usecase_async(GetStockItemsInputPort(), output_port, pipeline_configuration)
