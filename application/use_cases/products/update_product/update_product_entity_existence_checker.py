from clapy import EntityExistenceChecker

from application.services.ientity_existence_checker import IEntityExistenceChecker
from application.use_cases.products.update_product.iupdate_product_output_port import IUpdateProductOutputPort
from application.use_cases.products.update_product.update_product_input_port import UpdateProductInputPort
from domain.entities.product import Product


class UpdateProductEntityExistenceChecker(EntityExistenceChecker):

    def __init__(self, existence_checker: IEntityExistenceChecker):
        self.existence_checker = existence_checker

    async def execute_async(self, input_port: UpdateProductInputPort, output_port: IUpdateProductOutputPort):
        if not self.existence_checker.does_entity_exist(Product, input_port.product_id):
            self.has_failures = True
            await output_port.present_product_not_found_async(input_port.product_id)
