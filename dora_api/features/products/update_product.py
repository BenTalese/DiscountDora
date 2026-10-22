from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_historic_offer import ProductHistoricOffer
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import business_rule_violation, no_content, not_found
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool | None = None
    is_available: bool | None = None
    price_now: float | None = Field(default = None, gt = 0)
    price_was: float | None = Field(default = None, gt = 0)
    # Photo — custom products only (owner 2026-10-17: "are we able to set
    # images for custom products? Should only be able to for those."). Same
    # contract as Store / User: a `data:image/...;base64,...` string (already
    # resized + re-encoded by the client's `processImageFile` under the install
    # image policy, R-003), stored as UTF-8 bytes and served by
    # `GET /products/<id>/image`; `clear_image=True` removes it and wins over
    # `image`; `image=None` without the flag leaves the photo untouched.
    #
    # An ingested product's picture belongs to its source — the producer
    # supplies it and the next ingest may restate it — so a hand-set photo
    # there would be either silently overwritten or silently diverge from the
    # source. The handler refuses rather than guessing which.
    image: str | None = Field(default = None, max_length = 6_000_000)
    clear_image: bool = False
    # Settable on any product, ingested or custom: a scraper rarely knows how
    # many eggs are in the carton, and ingest only restates it when its source
    # does (a null push never clobbers). Sending `null` clears it (FU-856).
    pack_count: int | None = Field(default = None, gt = 0)


@dataclass(slots=True)
class UpdateProductResponse:
    product_not_found: bool = False
    incomplete_price_info: bool = False
    image_not_custom: bool = False
    invalid_image: bool = False


class UpdateProductHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: UpdateProductRequest, product_id: UUID) -> UpdateProductResponse:
        _Product: Product | None = (
            self.repository
            .get(Product)
            .include(Product.Fields.CURRENT_OFFER)
            .include(Product.Fields.HISTORIC_OFFERS)
            .by_id(product_id)
        )

        if not _Product:
            return UpdateProductResponse(product_not_found=True)

        _SetFields = request.model_fields_set
        _PriceNowSet = "price_now" in _SetFields and request.price_now is not None
        _PriceWasSet = "price_was" in _SetFields and request.price_was is not None

        if _PriceNowSet ^ _PriceWasSet:
            return UpdateProductResponse(incomplete_price_info=True)

        _ImageSet = "image" in _SetFields and request.image is not None
        if (_ImageSet or request.clear_image) and not _Product.is_custom:
            return UpdateProductResponse(image_not_custom=True)
        if _ImageSet and not request.image.startswith("data:image/"):
            return UpdateProductResponse(invalid_image=True)

        if "is_active" in _SetFields and request.is_active is not None:
            _Product.is_active = request.is_active

        if "is_available" in _SetFields and request.is_available is not None:
            _Product.is_available = request.is_available

        if "pack_count" in _SetFields:
            _Product.pack_count = request.pack_count

        if request.clear_image:
            _Product.image = None
        elif _ImageSet:
            _Product.image = request.image.encode("utf-8")

        if _PriceNowSet and _PriceWasSet:
            _HistoricOffer = ProductHistoricOffer(
                offered_on = _Product.current_offer.offered_on,
                price_now = _Product.current_offer.price_now,
                price_was = _Product.current_offer.price_was)

            _Product.historic_offers.append(_HistoricOffer)
            # Without repo.add() the cascaded insert carries EMPTY_UUID, so
            # the SECOND archived offer in an install's lifetime collides on
            # the primary key and 500s (the ingest path and seed both add()).
            self.repository.add(_HistoricOffer)

            _Product.current_offer.offered_on = datetime.now(UTC)
            _Product.current_offer.price_now = request.price_now
            _Product.current_offer.price_was = request.price_was

        self.repository.save_changes()
        return UpdateProductResponse()


@PRODUCT_ROUTER.route("<uuid:product_id>", methods=["PATCH"])
@has_request_body(UpdateProductRequest)
def update_product(product_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to update product.")
    _Handler = UpdateProductHandler(SqlAlchemyRepository())
    _Request: UpdateProductRequest = get_request_body()
    _Response = _Handler.handle(_Request, product_id)

    if _Response.product_not_found:
        _Logger.warning(f"Product not found with ID: {product_id}")
        return not_found(Product.__name__, product_id)

    if _Response.incomplete_price_info:
        _Logger.warning("price_now or price_was was set without the other.")
        return business_rule_violation("price_now and price_was must both be set.")

    if _Response.image_not_custom:
        _Logger.warning(f"Refused a photo change on non-custom product {product_id}.")
        return business_rule_violation(
            "Only products you added yourself can have their photo changed."
        )

    if _Response.invalid_image:
        return business_rule_violation(
            "The photo must be a 'data:image/<type>;base64,...' data URL."
        )

    _Logger.info(f"Successfully updated product with ID: {product_id}")
    return no_content()
