from typing import List

from clapy import PipeConfiguration

from application.use_cases.stock_locations.create_stock_location.create_stock_location_input_port import \
    CreateStockLocationInputPort
from application.use_cases.stock_locations.create_stock_location.icreate_stock_location_output_port import \
    ICreateStockLocationOutputPort

from .base_controller import BaseController, DEFAULT_PIPELINE


class StockLocationController(BaseController):
    
    async def create_stock_location_async(
            self,
            input_port: CreateStockLocationInputPort,
            output_port: ICreateStockLocationOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        self._use_case_invoker.invoke_usecase_async(input_port, output_port, pipeline_configuration)