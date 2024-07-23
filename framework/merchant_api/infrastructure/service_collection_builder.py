import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from clapy import DependencyInjectorServiceProvider
from dependency_injector import providers

from application.infrastructure.utils import get_classes_ending_with
from framework.merchant_api.infrastructure.configuration_manager import \
    ConfigurationManager
from framework.merchant_api.infrastructure.merchant_data_providers.coles_provider import \
    ColesProvider
from framework.merchant_api.infrastructure.merchant_data_providers.grocerize_provider import \
    GrocerizeProvider
from framework.merchant_api.infrastructure.merchant_data_providers.iga_provider import \
    IGAProvider
from framework.merchant_api.infrastructure.merchant_data_providers.save_on_groceries_provider import \
    SaveOnGroceriesProvider
from framework.merchant_api.infrastructure.merchant_data_providers.woolworths_provider import \
    WoolworthsProvider
from framework.merchant_api.services.iconfiguration_manager import \
    IConfigurationManager


class ServiceCollectionBuilder:
    def __init__(self, service_provider: DependencyInjectorServiceProvider):
        self.service_provider = service_provider

    def build_service_provider(self):
        return self \
            .register_configuration_provider() \
            .register_api_presenters() \
            .register_merchant_data_providers() \
            .register_logger() \
            .service_provider

    def register_api_presenters(self):
        for _Presenter in get_classes_ending_with('presenter', Path() / 'framework' / 'merchant_api' / 'routes'):
            self.service_provider.register_service(providers.Factory, _Presenter)
        return self

    def register_configuration_provider(self):
        self.service_provider.register_service(providers.Singleton, ConfigurationManager, IConfigurationManager)
        return self

    def register_merchant_data_providers(self):
        self.service_provider.register_service(providers.Singleton, ColesProvider)
        self.service_provider.register_service(providers.Singleton, IGAProvider)
        self.service_provider.register_service(providers.Singleton, GrocerizeProvider)
        self.service_provider.register_service(providers.Singleton, SaveOnGroceriesProvider)
        self.service_provider.register_service(providers.Singleton, WoolworthsProvider)
        return self

    def register_logger(self):
        _ConfigurationManager: IConfigurationManager = self.service_provider.get_service(IConfigurationManager)

        log_folder = Path() / 'logs'
        if not Path.exists(log_folder):
            Path.mkdir(log_folder)

        logger = logging.getLogger(__name__)
        log_filename = log_folder / 'mapi_logs.txt'
        file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=30)
        file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(lineno)04d | %(message)s'))
        logger.setLevel(_ConfigurationManager.get_log_level())
        logger.addHandler(file_handler)

        self.service_provider.register_service(providers.Object, logger)
        # FIXME: Clapy needs update to allow overriding the name of the service
        setattr(self.service_provider._container, "logging_Logger", providers.Object(logger))

        return self
