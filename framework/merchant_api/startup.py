import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from clapy import DependencyInjectorServiceProvider, IServiceProvider
from flask import Flask
from flask_cors import CORS

sys.path.append(os.getcwd())

from application.infrastructure.utils import get_attributes_ending_with
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
from framework.merchant_api.infrastructure.middleware import MIDDLEWARE
from framework.merchant_api.infrastructure.service_collection_builder import \
    ServiceCollectionBuilder
from framework.merchant_api.services.iconfiguration_manager import \
    IConfigurationManager
from framework.merchant_api.services.imerchant_data_provider import \
    IMerchantDataProvider


async def startup():
    _App = Flask(__name__)

    _ServiceProvider: IServiceProvider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()).build_service_provider()
    _App.service_provider = _ServiceProvider
    _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)

    WEB_APP_HOST = _ConfigurationManager.get_web_app_host()
    WEB_APP_PORT = _ConfigurationManager.get_web_app_port()

    CORS(_App, resources={r'/api/*': {'origins': f'http://{WEB_APP_HOST}:{WEB_APP_PORT}', "allow_headers": ["*", "Content-Type"]}})

    register_routers(_App)
    register_api_infrastructure(_App)

    scheduler = BackgroundScheduler()
    scheduler.add_job(data_provider_health_check, IntervalTrigger(days = 1), args = [_ServiceProvider])
    scheduler.start()

    data_provider_health_check(_ServiceProvider)

    _App.run(
        _ConfigurationManager.get_api_host(),
        _ConfigurationManager.get_api_port(),
        _ConfigurationManager.is_debug_mode_enabled(),
        use_reloader = _ConfigurationManager.is_reloader_enabled()
    )


def register_routers(app: Flask):
    for _Router in get_attributes_ending_with('router', Path() / 'framework' / 'merchant_api' / 'routes'):
        app.register_blueprint(_Router)


def register_api_infrastructure(app: Flask):
    app.register_blueprint(MIDDLEWARE)


def data_provider_health_check(service_provider: IServiceProvider):

    # TODO: Maybe make this a route that can be hit, also just call the route from here?
    # TODO: May need a delay here too

    _ConfigurationManager: IConfigurationManager = service_provider.get_service(IConfigurationManager)
    _Logger: logging.Logger = service_provider.get_service(logging.Logger)
    _MerchantDataProviders: List[IMerchantDataProvider] = [
        service_provider.get_service(ColesProvider),
        service_provider.get_service(IGAProvider),
        service_provider.get_service(GrocerizeProvider),
        service_provider.get_service(SaveOnGroceriesProvider),
        service_provider.get_service(WoolworthsProvider)
    ]

    _Merchants = _ConfigurationManager.get_all_merchants()

    for _MerchantDataProvider in _MerchantDataProviders:

        try:
            _Offers = _MerchantDataProvider.search_by_term(
                'Chocolate Ice Cream',
                next(_Merchant for _Merchant in _Merchants if _MerchantDataProvider.is_merchant_supported(_Merchant)),
                1)

            _MerchantDataProvider.is_healthy = bool(_Offers)

        except Exception as e:
            _MerchantDataProvider.is_healthy = False
            _Logger.exception(f"Merchant Data Provider '{_MerchantDataProvider.base_url}' encountered a problem.", e)


if __name__ == '__main__':
    asyncio.run(startup())
