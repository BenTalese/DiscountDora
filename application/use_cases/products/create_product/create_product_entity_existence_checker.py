from clapy import EntityExistenceChecker
from application.services.ientity_existence_checker import IEntityExistenceChecker

from application.use_cases.products.create_product.create_product_input_port import CreateProductInputPort
from application.use_cases.products.create_product.icreate_product_output_port import ICreateProductOutputPort


class CreateProductEntityExistenceChecker(EntityExistenceChecker):

    def __init__(self, existence_checker: IEntityExistenceChecker):
        self.existence_checker = existence_checker

    async def execute_async(self, input_port: CreateProductInputPort, output_port: ICreateProductOutputPort):
        if not self.existence_checker.does_entity_exist(input_port.merchant_id):
            self.has_failures = True
            await output_port.present_merchant_not_found_async(input_port.merchant_id)
