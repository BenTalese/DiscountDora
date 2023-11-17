from clapy import DependencyInjectorServiceProvider

from framework.persistence.infrastructure.configure_services import \
    configure_persistence_services
from interface_adaptors.infrastructure.configure_services import \
    configure_interface_adaptors_services


class ServiceCollectionBuilder:
    def __init__(self, service_provider: DependencyInjectorServiceProvider):
        self.service_provider = service_provider

    def build_service_provider(self):
        return self \
            .configure_persistence_services() \
            .configure_clapy_services() \
            .configure_core_services() \
            .service_provider

    def configure_core_services(self):
        configure_interface_adaptors_services(self.service_provider)
        return self

    def configure_clapy_services(self):
        self.service_provider.configure_clapy_services(["application/use_cases"], [r"venv", r"src"], [r".*main\.py"])
        return self

    def configure_persistence_services(self):
        configure_persistence_services(self.service_provider)
        return self
