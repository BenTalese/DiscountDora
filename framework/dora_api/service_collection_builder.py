import os

from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers

from application.infrastructure.configure_services import \
    configure_application_services
from application.infrastructure.utils import get_classes_ending_with
from domain.infrastructure.configure_services import configure_domain_services
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
            .configure_core_services() \
            .register_api_presenters() \
            .service_provider

    def register_api_presenters(self):
        for _Presenter in get_classes_ending_with('presenter', os.path.normpath('framework/api/routes')):
            self.service_provider.register_service(providers.Factory, _Presenter)

        return self

    def configure_core_services(self):
        configure_domain_services(self.service_provider)
        configure_application_services(self.service_provider)
        self.service_provider.configure_clapy_services([os.path.normpath('application/use_cases')], [r"venv", r"src"], [r".*main\.py"])
        configure_interface_adaptors_services(self.service_provider)
        return self

    def configure_persistence_services(self):
        configure_persistence_services(self.service_provider)
        return self
