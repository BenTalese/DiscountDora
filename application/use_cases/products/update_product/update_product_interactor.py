from datetime import datetime

from clapy import Interactor
from varname import nameof
from application.dtos.product_dto import get_product_dto

from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.products.update_product.iupdate_product_output_port import \
    IUpdateProductOutputPort
from application.use_cases.products.update_product.update_product_input_port import \
    UpdateProductInputPort
from domain.entities.product import Product
from domain.entities.product_offer import ProductOffer


class UpdateProductInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: UpdateProductInputPort, output_port: IUpdateProductOutputPort):
        _Product: Product = self.persistence_context \
            .get_entities(Product) \
            .include(nameof(Product.current_offer)) \
            .include(nameof(Product.historical_offers)) \
            .first_by_id(input_port.product_id)

        if input_port.is_available.has_been_set:
            _Product.is_available = input_port.is_available

        if input_port.price_now.has_been_set and input_port.price_was.has_been_set:
            _Product.historical_offers.append(ProductOffer(
                offered_on = _Product.current_offer.offered_on,
                price_now = _Product.current_offer.price_now,
                price_was = _Product.current_offer.price_was))

            _Product.current_offer = ProductOffer(
                offered_on = datetime.utcnow(),
                price_now = input_port.price_now,
                price_was = input_port.price_was)

        await output_port.present_product_updated_async(get_product_dto(_Product))
