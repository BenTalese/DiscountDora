from typing import List

from clapy import PipeConfiguration
from application.use_cases.stock_items.create_stock_item.create_stock_item_input_port import CreateStockItemInputPort
from application.use_cases.stock_items.create_stock_item.icreate_stock_item_output_port import ICreateStockItemOutputPort

from application.use_cases.stock_items.get_stock_items.get_stock_items_input_port import \
    GetStockItemsInputPort
from application.use_cases.stock_items.get_stock_items.iget_stock_items_output_port import \
    IGetStockItemsOutputPort

from .base_controller import DEFAULT_PIPELINE, BaseController


class StockItemController(BaseController):

    async def create_stock_item_async(
            self,
            input_port: CreateStockItemInputPort,
            output_port: ICreateStockItemOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        await self._use_case_invoker.invoke_usecase_async(input_port, output_port, pipeline_configuration)

    async def get_stock_items_async(
            self,
            output_port: IGetStockItemsOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        await self._use_case_invoker.invoke_usecase_async(GetStockItemsInputPort(), output_port, pipeline_configuration)
