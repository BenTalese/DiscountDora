from clapy.outputs import ValidationResult
from application.dtos.product_dto import ProductDto
from application.use_cases.products.update_product.iupdate_product_output_port import IUpdateProductOutputPort
from domain.entities.base_entity import EntityID


class UpdateProductPresenter(IUpdateProductOutputPort):
    result: ProductDto = None

    async def present_product_not_found_async(self, product_id: EntityID):
        raise NotImplementedError()

    async def present_product_updated_async(self, product: ProductDto):
        self.result = product

    async def present_validation_failure_async(self, validation_failure: ValidationResult):
        raise NotImplementedError()
