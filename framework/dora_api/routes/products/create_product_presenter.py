from varname import nameof
from application.dtos.product_dto import ProductDto
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.products.create_product.icreate_product_output_port import \
    ICreateProductOutputPort
from domain.entities.base_entity import EntityID
from framework.dora_api.infrastructure.base_presenter import BasePresenter
from framework.dora_api.routes.products.create_product_command import CreateProductCommand
from framework.dora_api.view_models.created_view_model import CreatedViewModel


class CreateProductPresenter(BasePresenter, ICreateProductOutputPort):

    def __init__(self, persistence: IPersistenceContext):
        self.persistence = persistence

    async def present_product_created_async(self, product: ProductDto):
        await self.persistence.save_changes_async()
        await self.created_async(CreatedViewModel(product.product_id.value))

    async def present_product_already_exists_async(self):
        self.request_body: CreateProductCommand
        await self.business_rule_violation_async(f'''A product with the stockcode '{self.request_body.merchant_stockcode}'
         from the merchant '{self.request_body.merchant_name}' already exists.''')

    async def present_merchant_not_found_async(self, merchant_id: EntityID):
        await self.entity_existence_failure_async(nameof(merchant_id), merchant_id.value)
