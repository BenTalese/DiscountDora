from pathlib import Path

from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers

from application.infrastructure.utils import get_classes_ending_with
from framework.merchant_api.infrastructure.configuration_provider import \
    ConfigurationProvider
from framework.merchant_api.services.iconfiguration_provider import \
    IConfigurationProvider


class ServiceCollectionBuilder:
    def __init__(self, service_provider: DependencyInjectorServiceProvider):
        self.service_provider = service_provider

    def build_service_provider(self):
        return self \
            .register_configuration_provider() \
            .register_api_presenters() \
            .service_provider

    def register_api_presenters(self):
        for _Presenter in get_classes_ending_with('presenter', Path() / 'framework' / 'merchant_api' / 'routes'):
            self.service_provider.register_service(providers.Factory, _Presenter)
        return self

    def register_configuration_provider(self):
        self.service_provider.register_service(providers.Singleton, ConfigurationProvider, IConfigurationProvider)
        return self
