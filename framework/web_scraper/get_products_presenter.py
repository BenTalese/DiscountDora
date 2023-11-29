from typing import List
from application.dtos.product_dto import ProductDto
from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.products.get_products.iget_products_output_port import IGetProductsOutputPort


class GetProductsPresenter(IGetProductsOutputPort):
    products: List[ProductDto] = None

    async def present_products_async(self, products: IQueryBuilder[ProductDto]):
        self.products = products.execute()
