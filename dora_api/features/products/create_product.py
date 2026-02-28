import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from varname import nameof

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.features.products.get_products import ProductDto, get_products
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import Field
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True, kw_only=True)
class CreateProductRequest:
    brand: str | None = None
    image: bytes | None = None
    is_active: bool
    is_available: bool
    merchant_name: str
    merchant_stockcode: str | None = None
    name: str
    price_now: float
    price_was: float
    size: str
    size_unit: str
    size_value: float
    web_url: str | None = None


@dataclass(slots=True)
class CreateProductResponse:
    new_product_id: EntityID = EntityID()
    product_already_exists: bool = False


class CreateProductHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateProductRequest) -> CreateProductResponse:
        _MerchantName = Field(Merchant, nameof(Merchant.name))
        _ProductName = Field(Product, nameof(Product.name))
        _ProductStockcode = Field(Product, nameof(Product.merchant_stockcode))
        _ProductStockcode = Field(Product, nameof(Product.merchant_stockcode))

        _ExistingProduct: Product | None = (
            self.repository
            .get(Product)
            .include(nameof(Product.merchant))  # TODO: Is this line necessary?
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

    _Logger.info(f"Successfully created product with ID: {_Response.new_product_id.value}")
    return created(
        _Response.new_product_id.value,
        f"{nameof(PRODUCT_ROUTER)}.{nameof(get_products)}",
        nameof(ProductDto.product_id)
    )
