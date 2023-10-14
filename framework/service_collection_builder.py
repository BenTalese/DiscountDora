from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers

from application.services.ipersistence_context import IPersistenceContext
from framework.persistence.infrastructure.persistence_context import \
    SqlAlchemyPersistenceContext
from interface_adaptors.controllers.stock_item_controller import \
    StockItemController


class ServiceCollectionBuilder:
    def __init__(self, service_provider: DependencyInjectorServiceProvider):
        self.service_provider = service_provider

    def configure_application_services(self):
        return self

    def configure_clapy_services(self):
        self.service_provider.configure_clapy_services(["application/use_cases"], [r"venv", r"src"], [r".*main\.py"])
        return self

    def configure_interface_adaptors_services(self):
        self.service_provider.register_service(providers.Factory, StockItemController)
        return self

    def configure_persistence_services(self):
        self.service_provider.register_service(providers.Factory, SqlAlchemyPersistenceContext, IPersistenceContext)
        return self
