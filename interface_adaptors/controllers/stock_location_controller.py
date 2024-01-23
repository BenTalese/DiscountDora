from typing import List

from clapy import PipeConfiguration

from application.use_cases.stock_locations.create_stock_location.create_stock_location_input_port import \
    CreateStockLocationInputPort
from application.use_cases.stock_locations.create_stock_location.icreate_stock_location_output_port import \
    ICreateStockLocationOutputPort

from application.use_cases.stock_locations.delete_stock_location.delete_stock_location_input_port import \
    DeleteStockLocationInputPort
from application.use_cases.stock_locations.delete_stock_location.idelete_stock_location_output_port import \
    IDeleteStockLocationOutputPort

from application.use_cases.stock_locations.get_stock_locations.get_stock_locations_input_port import \
    GetStockLocationsInputPort
from application.use_cases.stock_locations.get_stock_locations.iget_stock_locations_output_port import \
    IGetStockLocationsOutputPort

from .base_controller import BaseController, DEFAULT_PIPELINE


class StockLocationController(BaseController):
    
    async def create_stock_location_async(
            self,
            input_port: CreateStockLocationInputPort,
            output_port: ICreateStockLocationOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        await self._use_case_invoker.invoke_usecase_async(input_port, output_port, pipeline_configuration)

    async def delete_stock_location_async(
            self,
            input_port: DeleteStockLocationInputPort,
            output_port: IDeleteStockLocationOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        await self._use_case_invoker.invoke_usecase_async(input_port, output_port, pipeline_configuration)

    async def get_stock_locations_async(
            self,
            output_port: IGetStockLocationsOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        await self._use_case_invoker.invoke_usecase_async(GetStockLocationsInputPort(), output_port, pipeline_configuration)
