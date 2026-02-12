from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.products.get_products.iget_products_output_port import IGetProductsOutputPort
from domain.entities.product import Product
from framework.dora_api.infrastructure.base_presenter import BasePresenter
from framework.dora_api.view_models.product_view_model import get_product_view_model


class GetProductsPresenter(BasePresenter, IGetProductsOutputPort):
    async def present_products_async(self, products: IQueryBuilder[Product]):
        await self.ok_async(products.project(get_product_view_model).execute())
