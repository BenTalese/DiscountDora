from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers

from interface_adaptors.controllers.merchant_controller import MerchantController
from interface_adaptors.controllers.product_controller import ProductController
from interface_adaptors.controllers.stock_item_controller import StockItemController
from interface_adaptors.controllers.stock_location_controller import StockLocationController
from interface_adaptors.controllers.user_controller import UserController


def configure_interface_adaptors_services(service_provider: DependencyInjectorServiceProvider) -> None:
    service_provider.register_service(providers.Factory, MerchantController)
    service_provider.register_service(providers.Factory, ProductController)
    service_provider.register_service(providers.Factory, StockItemController)
    service_provider.register_service(providers.Factory, StockLocationController)
    service_provider.register_service(providers.Factory, UserController)
