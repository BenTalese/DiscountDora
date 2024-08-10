import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from clapy import DependencyInjectorServiceProvider, IServiceProvider
from flask import Flask
from flask_cors import CORS

sys.path.append(os.getcwd())

from application.infrastructure.utils import get_attributes_ending_with
from framework.merchant_api.infrastructure.merchant_data_providers import \
    get_merchant_data_providers
from framework.merchant_api.infrastructure.middleware import MIDDLEWARE
from framework.merchant_api.infrastructure.service_collection_builder import \
    ServiceCollectionBuilder
from framework.merchant_api.services.iconfiguration_manager import \
    IConfigurationManager


async def startup():
    _App = Flask(__name__)

    _ServiceProvider: IServiceProvider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()).build_service_provider()
    _App.service_provider = _ServiceProvider
    _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)

    WEB_APP_HOST = _ConfigurationManager.get_web_app_host()
    WEB_APP_PORT = _ConfigurationManager.get_web_app_port()

    CORS(_App, resources={r'/api/*': {'origins': f'http://{WEB_APP_HOST}:{WEB_APP_PORT}', "allow_headers": ["*", "Content-Type"]}})

    configure_logger(_ConfigurationManager.get_log_level())
    register_routers(_App)
    register_api_infrastructure(_App)

    scheduler = BackgroundScheduler()
    scheduler.add_job(data_provider_cron_health_check, IntervalTrigger(days = 1), args = [_ServiceProvider])
    scheduler.start()

    _App.run(
        _ConfigurationManager.get_api_host(),
        _ConfigurationManager.get_api_port(),
        _ConfigurationManager.is_debug_mode_enabled(),
        use_reloader = _ConfigurationManager.is_reloader_enabled()
    )


def configure_logger(log_level: int):
    _LogFolder = Path() / 'logs' / 'merchant_api'
    if not Path.exists(_LogFolder):
        Path.mkdir(_LogFolder)

    _Logger = logging.getLogger()
    _LogFilename = _LogFolder / 'log.txt'
    _FileHandler = TimedRotatingFileHandler(_LogFilename, when="midnight", interval=1, backupCount=30)
    _FileHandler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(lineno)04d | %(message)s'))
    _Logger.setLevel(log_level)
    _Logger.addHandler(_FileHandler)


def register_routers(app: Flask):
    for _Router in get_attributes_ending_with('router', Path() / 'framework' / 'merchant_api' / 'routes'):
        app.register_blueprint(_Router)


def register_api_infrastructure(app: Flask):
    app.register_blueprint(MIDDLEWARE)


def data_provider_cron_health_check(service_provider: IServiceProvider):
    _ConfigurationManager: IConfigurationManager = service_provider.get_service(IConfigurationManager)
    _Logger = logging.getLogger(__name__)
    _DataProviders = get_merchant_data_providers()
    _Merchants = _ConfigurationManager.get_all_merchants()
    _Logger.info("Running health check for merchant data providers.")

    for _MerchantDataProvider in _DataProviders:

        try:
            _Offers = _MerchantDataProvider.search_by_term(
                'Chocolate Ice Cream',
                next(_Merchant for _Merchant in _Merchants if _MerchantDataProvider.is_merchant_supported(_Merchant)),
                1)

            _MerchantDataProvider.is_healthy = bool(_Offers)
            _Logger.info(
                f"Merchant Data Provider '{_MerchantDataProvider.base_url}' is {'HEALTHY' if _MerchantDataProvider.is_healthy else 'NOT HEALTHY'}."
            )

        except Exception as e:
            _MerchantDataProvider.is_healthy = False
            _Logger.exception(f"Merchant Data Provider '{_MerchantDataProvider.base_url}' encountered a problem.", e)


if __name__ == '__main__':
    asyncio.run(startup())
