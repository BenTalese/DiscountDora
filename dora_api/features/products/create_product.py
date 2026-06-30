import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.store import Store
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.ingestion.offer_mapping import (OfferOutcome,
                                                       apply_offer_to_product)
from dora_api.features.products.get_products import get_products
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import business_rule_violation, created
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class CreateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: str | None = Field(default = None, min_length = 1)
    # FU-014 — image is a data-URL string ("data:image/...;base64,..."), stored
    # as UTF-8 bytes on the entity; served back via GET /products/<id>/image.
    # Matches the stock-item/recipe convention. The old `Base64Bytes` decoded
    # arbitrary base64 strings to raw bytes that the read path then tried to
    # `decode('utf-8','ignore')` — corrupting every saved image.
    image: str | None = Field(default = None, max_length = 6_000_000)
    is_active: bool
    is_available: bool
    store_name: str = Field(min_length = 1)
    # FU-189 carve-out: `merchant_stockcode` is the producer's SKU on the
    # offer, retained verbatim per the rename runbook.
    merchant_stockcode: str | None = Field(default = None, min_length = 1)
    name: str = Field(min_length = 1)
    price_now: float = Field(gt = 0)
    price_was: float = Field(gt = 0)
    size: str = Field(min_length = 1)
    size_unit: str = Field(min_length = 1)
    size_value: float = Field(gt = 0)
    web_url: str | None = Field(default = None, min_length = 1)


# FU-217 / R-003 — the manual product-add reuses the C-10 shared
# `apply_offer_to_product` so duplicates append a historic point + move
# `current_offer` (one offer-append path across `/api/products` and
# `/api/ingest`). Source string is `"manual"` to distinguish from
# ingest-provenance points.
_MANUAL_SOURCE = "manual"


@dataclass(slots=True)
class CreateProductResponse:
    product_id: UUID = EMPTY_UUID
    created: bool = False
    offer_appended: bool = False
    store_not_found: bool = False


class CreateProductHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateProductRequest) -> CreateProductResponse:
        _StoreName = EntityField(Store, Store.Fields.NAME)
        _ProductName = EntityField(Product, Product.Fields.NAME)
        _ProductStockcode = EntityField(Product, Product.Fields.MERCHANT_STOCKCODE)

        # FU-189a — strict no-auto-create. Stores are user-curated (managed
        # in Settings → Stores); the manual product-add path must reject
        # unknown store names, mirroring what `/api/ingest` already does via
        # the quarantine queue (FU-190). Case-insensitive trimmed match to
        # mirror `CreateStoreHandler`'s duplicate-detection semantics so
        # callers aren't surprised by casing.
        _NormalisedName = request.store_name.strip().lower()
        _Store: Store | None = next(
            (s for s in self.repository.get(Store).all()
             if s.name.strip().lower() == _NormalisedName),
            None,
        )
        if _Store is None:
            return CreateProductResponse(store_not_found=True)

        _ExistingProduct: Product | None = (
            self.repository
            .get(Product)
            .include(Product.Fields.STORE)
            .include(Product.Fields.CURRENT_OFFER)
            .one(_ProductStockcode.eq(request.merchant_stockcode)
                 & _StoreName.eq(_Store.name)
                 & _ProductName.eq(request.name))
        )

        observed_at = datetime.now(UTC)

        if _ExistingProduct is not None:
            outcome = apply_offer_to_product(
                self.repository,
                _ExistingProduct,
                price_now=request.price_now,
                price_was=request.price_was,
                observed_at=observed_at,
                source=_MANUAL_SOURCE,
            )
            self.repository.save_changes()
            return CreateProductResponse(
                product_id=_ExistingProduct.id,
                created=False,
                offer_appended=outcome.outcome == OfferOutcome.APPENDED,
            )

        _Offer = ProductOffer(
            offered_on=observed_at,
            price_now=request.price_now,
            price_was=request.price_was,
        )
        _NewProduct = Product(
            brand=request.brand,
            current_offer=_Offer,
            historic_offers=[],
            image=request.image.encode("utf-8") if request.image else None,
            is_active=request.is_active,
            is_available=request.is_available,
            store=_Store,
            merchant_stockcode=request.merchant_stockcode,
            name=request.name,
            size=request.size,
            size_unit=request.size_unit,
            size_value=request.size_value,
            web_url=request.web_url,
        )

        self.repository.add(_Offer)
        self.repository.add(_NewProduct)
        self.repository.save_changes()

        return CreateProductResponse(
            product_id=_NewProduct.id,
            created=True,
            offer_appended=False,
        )


@PRODUCT_ROUTER.route("", methods=["POST"])
@has_request_body(CreateProductRequest)
def create_product():
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(CreateProductHandler)
    _Request: CreateProductRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.store_not_found:
        _Logger.warning(
            f"Rejected product create — unknown store '{_Request.store_name}'."
        )
        return business_rule_violation(
            f"Store '{_Request.store_name}' does not exist. "
            "Create it in Settings → Stores first."
        )

    if _Response.created:
        _Logger.info(f"Created product {_Response.product_id}")
    elif _Response.offer_appended:
        _Logger.info(
            f"Appended new offer to existing product {_Response.product_id}"
        )
    else:
        _Logger.info(
            f"Existing product {_Response.product_id} already has this offer; no-op."
        )

    return created(
        _Response.product_id,
        f"{PRODUCT_ROUTER.name}.{get_products.__name__}",
        "product_id",
        body={
            "id": _Response.product_id,
            "created": _Response.created,
            "offer_appended": _Response.offer_appended,
        },
    )
