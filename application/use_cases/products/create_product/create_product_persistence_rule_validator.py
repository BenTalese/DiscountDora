from clapy import PersistenceRuleValidator
from domain.entities.merchant import Merchant
from domain.entities.product import Product
from varname import nameof

from application.services.irepository import IPersistenceContext
from application.use_cases.products.create_product.create_product_input_port import \
    CreateProductInputPort
from application.use_cases.products.create_product.icreate_product_output_port import \
    ICreateProductOutputPort
from dora_api.infrastructure.bool_operation import And, Equal


class CreateProductPersistenceRuleValidator(PersistenceRuleValidator):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: CreateProductInputPort, output_port: ICreateProductOutputPort):
        _Product: Product = self.persistence_context \
            .get_entities(Product) \
            .include(nameof(Product.merchant)) \
            .first_or_none(And(
                Equal((Product, nameof(Product.merchant_stockcode)), input_port.merchant_stockcode, is_case_insensitive = True),
                Equal((Merchant, nameof(Merchant.name)), input_port.merchant_name, is_case_insensitive = True)
            ))

        if _Product:
            self.has_failures = True
            await output_port.present_product_already_exists_async()
