from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from varname import nameof

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_historic_offer import ProductHistoricOffer
from dora_api.domain.types import UNSET, Unset
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import business_rule_violation, no_content, not_found
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body, is_set
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool | Unset = UNSET
    is_available: bool | Unset = UNSET
    price_now: float | Unset = Field(default = UNSET, gt = 0)
    price_was: float | Unset = Field(default = UNSET, gt = 0)


@dataclass(slots=True)
class UpdateProductResponse:
    product_not_found: bool = False
    incomplete_price_info: bool = False


class UpdateProductHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateProductRequest, product_id: UUID) -> UpdateProductResponse:
        # Get existing product
        _Product: Product | None = (
            self.repository
            .get(Product)
            .include(nameof(Product.current_offer))
            .include(nameof(Product.historic_offers))
            .by_id(product_id)
        )

        if not _Product:
            return UpdateProductResponse(product_not_found=True)

        # Validate price now / price was
        if is_set(request.price_now) ^ is_set(request.price_was):
            return UpdateProductResponse(incomplete_price_info=True)

        # Update product attributes
        if is_set(request.is_active):
            _Product.is_active = request.is_active

        if is_set(request.is_available):
            _Product.is_available = request.is_available

        if is_set(request.price_now) and is_set(request.price_was):
            _HistoricOffer = ProductHistoricOffer(
                offered_on = _Product.current_offer.offered_on,
                price_now = _Product.current_offer.price_now,
                price_was = _Product.current_offer.price_was)

            _Product.historic_offers.append(_HistoricOffer)

            _Product.current_offer.offered_on = datetime.now(UTC)
            _Product.current_offer.price_now = request.price_now
            _Product.current_offer.price_was = request.price_was

        self.repository.save_changes()
        return UpdateProductResponse()


@PRODUCT_ROUTER.route("<product_id>", methods=["PATCH"])
@has_request_body(UpdateProductRequest)
def update_product(product_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to update product.")
    _Handler = get_container().inject(UpdateProductHandler)
    _Request: UpdateProductRequest = get_request_body()
    _Response = _Handler.handle(_Request, product_id)

    if _Response.product_not_found:
        _Logger.warning(f"Product not found with ID: {product_id}")
        return not_found(nameof(Product), product_id)

    if _Response.incomplete_price_info:
        _Logger.warning("price_now or price_was was set without the other.")
        return business_rule_violation("price_now and price_was must both be set.")

    _Logger.info(f"Successfully updated product with ID: {product_id}")
    return no_content()
