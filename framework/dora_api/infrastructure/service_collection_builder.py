from pathlib import Path

from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers

from application.infrastructure.configure_services import \
    configure_application_services
from application.infrastructure.utils import get_classes_ending_with
from domain.infrastructure.configure_services import configure_domain_services
from framework.dora_api.infrastructure.configuration_manager import \
    ConfigurationManager
from framework.dora_api.persistence.configure_services import \
    configure_persistence_services
from framework.dora_api.services.iconfiguration_manager import \
    IConfigurationManager
from interface_adaptors.infrastructure.configure_services import \
    configure_interface_adaptors_services


class ServiceCollectionBuilder:
    def __init__(self, service_provider: DependencyInjectorServiceProvider):
        self.service_provider = service_provider

    def build_service_provider(self):
        return self \
            .register_configuration_manager() \
            .configure_persistence_services() \
            .configure_core_services() \
            .register_api_presenters() \
            .service_provider

    def configure_core_services(self):
        configure_domain_services(self.service_provider)
        configure_application_services(self.service_provider)
        self.service_provider.configure_clapy_services([Path() / 'application' / 'use_cases'], [r"venv", r"src"], [r".*main\.py"])
        configure_interface_adaptors_services(self.service_provider)
        return self

    def configure_persistence_services(self):
        configure_persistence_services(self.service_provider)
        return self

    def register_api_presenters(self):
        for _Presenter in get_classes_ending_with('presenter', Path() / 'framework' / 'dora_api' / 'routes'):
            self.service_provider.register_service(providers.Factory, _Presenter)
        return self

    def register_configuration_manager(self):
        self.service_provider.register_service(providers.Singleton, ConfigurationManager, IConfigurationManager)
        return self
