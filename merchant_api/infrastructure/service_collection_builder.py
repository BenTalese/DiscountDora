from pathlib import Path

from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers

from application.infrastructure.utils import get_classes_ending_with
from framework.merchant_api.infrastructure.configuration_manager import \
    ConfigurationManager
from framework.merchant_api.infrastructure.product_image_provider import \
    ProductImageProvider
from framework.merchant_api.services.iconfiguration_manager import \
    IConfigurationManager
from framework.merchant_api.services.iproduct_image_provider import \
    IProductImageProvider


class ServiceCollectionBuilder:
    def __init__(self, service_provider: DependencyInjectorServiceProvider):
        self.service_provider = service_provider

    def build_service_provider(self):
        self.service_provider.register_service(providers.Singleton, ConfigurationManager, IConfigurationManager)
        self.service_provider.register_service(providers.Singleton, ProductImageProvider, IProductImageProvider)

        for _Provider in get_classes_ending_with('provider', Path() / 'framework' / 'merchant_api' / 'infrastructure' / 'merchant_data_providers'):
            self.service_provider.register_service(providers.Singleton, _Provider)

        for _Presenter in get_classes_ending_with('presenter', Path() / 'framework' / 'merchant_api' / 'routes'):
            self.service_provider.register_service(providers.Factory, _Presenter)

        return self.service_provider
