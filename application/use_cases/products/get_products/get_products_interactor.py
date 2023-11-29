from clapy import Interactor
from application.dtos.product_dto import get_product_dto

from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.products.get_products.get_products_input_port import GetProductsInputPort
from application.use_cases.products.get_products.iget_products_output_port import IGetProductsOutputPort
from domain.entities.product import Product


class GetProductsInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: GetProductsInputPort, output_port: IGetProductsOutputPort):
        await output_port \
            .present_products_async(self.persistence_context
                                       .get_entities(Product)
                                       .project(get_product_dto))
