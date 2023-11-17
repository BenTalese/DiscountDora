from datetime import datetime
from clapy import Interactor
from application.dtos.product_dto import get_product_dto
from application.infrastructure.bool_operation import Equal
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.products.create_product.create_product_input_port import CreateProductInputPort
from varname import nameof

from application.use_cases.products.create_product.icreate_product_output_port import ICreateProductOutputPort
from domain.entities.merchant import Merchant
from domain.entities.product import Product
from domain.entities.product_offer import ProductOffer


class CreateProductInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: CreateProductInputPort, output_port: ICreateProductOutputPort):
        merchant = self.persistence_context.get_entities(Merchant).first(Equal(input_port.merchant_id, nameof(Merchant.id)))

        product = Product(
            brand = input_port.brand,
            current_offer = ProductOffer(
                offered_on = datetime.utcnow,
                price_now = input_port.price_now,
                price_was = input_port.price_was
            ),
            image = input_port.image,
            is_available = input_port.is_available,
            merchant = merchant,
            merchant_stockcode = input_port.merchant_stockcode,
            name = input_port.name,
            size_unit = input_port.size_unit,
            size_value = input_port.size_value,
            web_url = input_port.web_url
        )

        self.persistence_context.add(product)

        output_port.present_product_created_async(get_product_dto(product))
