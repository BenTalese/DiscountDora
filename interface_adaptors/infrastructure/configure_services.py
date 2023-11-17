from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers

from application.infrastructure.configure_services import \
    configure_application_services
from interface_adaptors.controllers.stock_item_controller import StockItemController


def configure_interface_adaptors_services(service_provider: DependencyInjectorServiceProvider) -> None:
    service_provider.register_service(providers.Factory, StockItemController)
    configure_application_services(service_provider)
