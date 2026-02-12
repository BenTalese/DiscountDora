from varname import nameof

from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.products.update_product.iupdate_product_output_port import \
    IUpdateProductOutputPort
from domain.entities.base_entity import EntityID
from domain.entities.product import Product
from framework.dora_api.infrastructure.base_presenter import BasePresenter


class UpdateProductPresenter(BasePresenter, IUpdateProductOutputPort):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def present_product_not_found_async(self, product_id: EntityID):
        await self.not_found_async(nameof(Product), product_id.value, 0)

    async def present_product_updated_async(self, product: Product):
        await self.persistence_context.save_changes_async()
        await self.no_content_async()
