from typing import List
from clapy import PipeConfiguration
from application.use_cases.products.create_product.create_product_input_port import CreateProductInputPort
from application.use_cases.products.create_product.icreate_product_output_port import ICreateProductOutputPort
from .base_controller import DEFAULT_PIPELINE, BaseController


class ProductController(BaseController):

    async def create_product_async(
            self,
            input_port: CreateProductInputPort,
            output_port: ICreateProductOutputPort,
            pipeline_configuration: List[PipeConfiguration] = DEFAULT_PIPELINE):
        await self._use_case_invoker.invoke_usecase_async(input_port, output_port, pipeline_configuration)
