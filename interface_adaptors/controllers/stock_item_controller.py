from typing import List

from clapy import PipeConfiguration

from application.pipeline.pipeline_configuration import PipelineConfiguration
from application.use_cases.stock_items.get_stock_items.get_stock_items_input_port import \
    GetStockItemsInputPort
from application.use_cases.stock_items.get_stock_items.iget_stock_items_output_port import \
    IGetStockItemsOutputPort

from .base_controller import BaseController


class StockItemController(BaseController):

    default_config = PipelineConfiguration.DefaultConfiguration.value

    async def get_stock_items_async(
            self,
            output_port: IGetStockItemsOutputPort,
            pipeline_configuration: List[PipeConfiguration] = default_config):
        await self._use_case_invoker.invoke_usecase_async(GetStockItemsInputPort(), output_port, pipeline_configuration)
