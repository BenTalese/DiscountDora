import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field

from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.products.get_products import get_products
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class CreateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: str | None = Field(default = None, min_length = 1)
    image: Base64Bytes | None = None
    is_active: bool
    is_available: bool
    merchant_name: str = Field(min_length = 1)
    merchant_stockcode: str | None = Field(default = None, min_length = 1)
    name: str = Field(min_length = 1)
    price_now: float = Field(gt = 0)
    price_was: float = Field(gt = 0)
    size: str = Field(min_length = 1)
    size_unit: str = Field(min_length = 1)
    size_value: float = Field(gt = 0)
    web_url: str | None = Field(default = None, min_length = 1)


@dataclass(slots=True)
class CreateProductResponse:
    new_product_id: UUID = EMPTY_UUID
    product_already_exists: bool = False


class CreateProductHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateProductRequest) -> CreateProductResponse:
        _MerchantName = EntityField(Merchant, Merchant.Fields.NAME)
        _ProductName = EntityField(Product, Product.Fields.NAME)
        _ProductStockcode = EntityField(Product, Product.Fields.MERCHANT_STOCKCODE)

        _ExistingProduct: Product | None = (
            self.repository
            .get(Product)
            .include(Product.Fields.MERCHANT)  # TODO: Is this line necessary?
            .one(_ProductStockcode.eq(request.merchant_stockcode)
                 & _MerchantName.eq(request.merchant_name)
                 & _ProductName.eq(request.name))
        )

        if _ExistingProduct:
            return CreateProductResponse(product_already_exists=True)

        _Merchant = self.repository.get(Merchant).one(_MerchantName.eq(request.merchant_name))
        if not _Merchant:
            _Merchant = Merchant(request.merchant_name)
            self.repository.add(_Merchant)

        _Offer = ProductOffer(
            offered_on = datetime.now(UTC),
            price_now = request.price_now,
            price_was = request.price_was
        )
        _NewProduct = Product(
            brand = request.brand,
            current_offer = _Offer,
            historic_offers = [],
            image = request.image,
            is_active = request.is_active,
            is_available = request.is_available,
            merchant = _Merchant,
            merchant_stockcode = request.merchant_stockcode,
            name = request.name,
            size = request.size,
            size_unit = request.size_unit,
            size_value = request.size_value,
            web_url = request.web_url
        )

        self.repository.add(_Offer)
        self.repository.add(_NewProduct)
        self.repository.save_changes()

        return CreateProductResponse(new_product_id = _NewProduct.id)


@PRODUCT_ROUTER.route("", methods=["POST"])
@has_request_body(CreateProductRequest)
def create_product():
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to create product.")
    _Handler = get_container().inject(CreateProductHandler)
    _Request: CreateProductRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.product_already_exists:
        _Logger.warning(
            f"Product already exists with name '{_Request.name}', "
            f"merchant '{_Request.merchant_name}', and "
            f"stockcode '{_Request.merchant_stockcode}'."
        )
        return business_rule_violation(
            f"Product already exists with name '{_Request.name}', "
            f"merchant '{_Request.merchant_name}', and "
            f"stockcode '{_Request.merchant_stockcode}'."
        )

    _Logger.info(f"Successfully created product with ID: {_Response.new_product_id}")
    return created(
        _Response.new_product_id,
        f"{PRODUCT_ROUTER.name}.{get_products.__name__}",
        "product_id",
    )
