from dataclasses import dataclass
from datetime import UTC, datetime
import logging

from varname import nameof

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.features.products.get_products import ProductDto, get_products
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import created, internal_server_error
from dora_api.infrastructure.bool_operation import And, Equal
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.services.irepository import IRepository


@dataclass(init=False, slots=True)
class CreateProductRequest:
    brand: str | None
    image: bytes | None
    is_active: bool
    is_available: bool
    merchant_name: str
    merchant_stockcode: str | None
    name: str
    price_now: float
    price_was: float
    size: str
    size_unit: str
    size_value: float | None
    web_url: str | None


@dataclass(slots=True)
class CreateProductResponse:
    new_product_id: EntityID | None = None
    product_already_exists: bool = False


class CreateProductHandler:
    def __init__(
            self,
            product_repository: IRepository[Product],
            merchant_repository: IRepository[Merchant]):
        self.product_repository = product_repository
        self.merchant_repository = merchant_repository

    def handle(self, request: CreateProductRequest) -> CreateProductResponse:
        # FIXME: This "existing" check won't work for custom products because
        # the user may not care for the merchant code, therefore is blank,
        # therefore easily multiple "blank" codes under same merchant...
        # Fix...maybe include product name?
        _ExistingProduct: Product | None = (
            self.product_repository
            .get()
            .include(nameof(Product.merchant))  # TODO: Is this line necessary?
            .one(And(
                # Equal((Product, nameof(Product.name)), request.name, is_case_insensitive = True),
                Equal((Product, nameof(Product.merchant_stockcode)), request.merchant_stockcode, is_case_insensitive = True),
                Equal((Merchant, nameof(Merchant.name)), request.merchant_name, is_case_insensitive = True)
            ))  # TODO: Maybe make case_sensitive and default off
        )

        if _ExistingProduct:
            return CreateProductResponse(product_already_exists=True)

        _Merchant = self.merchant_repository.get().one(Equal((Merchant, nameof(Merchant.name)), request.merchant_name))
        if not _Merchant:
            _Merchant = Merchant(request.merchant_name)
            self.merchant_repository.add(_Merchant)
            self.merchant_repository.save_changes()  # TODO: Investigate if can delay save and just use one because it's the same context underneath??

        _NewProduct = Product(
            brand = request.brand,
            current_offer = ProductOffer(
                offered_on = datetime.now(UTC),
                price_now = request.price_now,
                price_was = request.price_was
            ),
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

        self.product_repository.add(_NewProduct)
        self.product_repository.save_changes()

        return CreateProductResponse(new_product_id = _NewProduct.id)


@PRODUCT_ROUTER.route("", methods=["POST"])
@has_request_body(CreateProductRequest)
def create_product():
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to create product.")
    _Handler = get_container().inject(CreateProductHandler)
    _Request: CreateProductRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    # FIXME: Fix this check (see above)
    # if _Response.product_already_exists:
    #     _Logger.warning(f"Product already exists: {???}")
    #     return business_rule_violation(f"???")

    if _Response.new_product_id is None:
        _Logger.error("An unknown error occurred while creating the product.")
        return internal_server_error("An unknown error occurred while creating the product.")

    _Logger.info(f"Successfully created product with ID: {_Response.new_product_id.value}")
    return created(
        _Response.new_product_id.value,
        f"{nameof(PRODUCT_ROUTER)}.{nameof(get_products)}",
        nameof(ProductDto.product_id)
    )
