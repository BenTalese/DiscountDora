from application.dtos.product_dto import ProductDto
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.products.create_product.icreate_product_output_port import \
    ICreateProductOutputPort
from domain.entities.base_entity import EntityID
from framework.api.base_presenter import BasePresenter
from framework.api.view_models.created_view_model import CreatedViewModel


class CreateProductPresenter(BasePresenter, ICreateProductOutputPort):

    def __init__(self, persistence: IPersistenceContext):
        self.persistence = persistence

    async def present_product_created_async(self, product: ProductDto):
        await self.persistence.save_changes_async()
        await self.created_async(CreatedViewModel(product.id.value))

    async def present_merchant_not_found_async(self, merchant_id: EntityID):
        await self.entity_existence_failure_async(merchant_id.__name__, merchant_id.value)
