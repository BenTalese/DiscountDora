from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from uuid import UUID

from varname import nameof

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_historic_offer import ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.types import AttributeChangeTracker
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import business_rule_violation, no_content, not_found
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.services.irepository import IRepository


@dataclass(init=False, slots=True)
class UpdateProductRequest:
    is_active: AttributeChangeTracker[bool] = AttributeChangeTracker[bool]()
    is_available: AttributeChangeTracker[bool] = AttributeChangeTracker[bool]()
    price_now: AttributeChangeTracker[float] = AttributeChangeTracker[float]()
    price_was: AttributeChangeTracker[float] = AttributeChangeTracker[float]()


@dataclass(slots=True)
class UpdateProductResponse:
    product_not_found: bool = False
    price_now_or_price_was_set_without_the_other: bool = False


class UpdateProductHandler:
    def __init__(
            self,
            product_repository: IRepository[Product],
            product_offer_repository: IRepository[ProductOffer]):
        self.product_repository = product_repository
        self.product_offer_repository = product_offer_repository

    def handle(self, request: UpdateProductRequest, product_id: EntityID) -> UpdateProductResponse:
        # Get existing product
        _Product: Product | None = (
            self.product_repository
            .get()
            .include(nameof(Product.current_offer))
            .include(nameof(Product.historic_offers))
            .by_id(product_id))

        if not _Product:
            return UpdateProductResponse(product_not_found=True)

        # Validate price now / price was
        _PriceNowWithoutPriceWas = (
            request.price_now.has_been_set and not request.price_was.has_been_set
        )
        _PriceWasWithoutPriceNow = (
            request.price_was.has_been_set and not request.price_now.has_been_set
        )
        if _PriceNowWithoutPriceWas or _PriceWasWithoutPriceNow:
            return UpdateProductResponse(price_now_or_price_was_set_without_the_other=True)

        # Update product attributes
        if request.is_active.has_been_set:
            _Product.is_active = request.is_active.value

        if request.is_available.has_been_set:
            _Product.is_available = request.is_available.value

        if request.price_now.has_been_set and request.price_was.has_been_set:
            _HistoricOffer = ProductHistoricOffer(
                offered_on = _Product.current_offer.offered_on,
                price_now = _Product.current_offer.price_now,
                price_was = _Product.current_offer.price_was)

            _Product.historic_offers.append(_HistoricOffer)

            _Product.current_offer.offered_on = datetime.now(UTC)
            _Product.current_offer.price_now = request.price_now.value
            _Product.current_offer.price_was = request.price_was.value
            self.product_offer_repository.update(_Product.current_offer)  # FIXME: Surely it doesn't need to be like this?
            self.product_offer_repository.save_changes()

        self.product_repository.update(_Product)
        self.product_repository.save_changes()
        return UpdateProductResponse()


@PRODUCT_ROUTER.route("<product_id>", methods=["PATCH"])
@has_request_body(UpdateProductRequest)
def update_product(product_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to update product.")
    _Handler = get_container().inject(UpdateProductHandler)
    _Request: UpdateProductRequest = get_request_body()
    _Response = _Handler.handle(_Request, EntityID(product_id))

    if _Response.product_not_found:
        _Logger.warning(f"Product not found with ID: {product_id}")
        return not_found(nameof(Product), product_id)

    if _Response.price_now_or_price_was_set_without_the_other:
        _Logger.warning("price_now or price_was was set without the other.")
        return business_rule_violation("price_now and price_was must both be set.")

    _Logger.info(f"Successfully updated product with ID: {product_id}")
    return no_content()
