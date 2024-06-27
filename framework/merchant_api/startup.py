import asyncio
import os
import sys
from pathlib import Path

from clapy import DependencyInjectorServiceProvider, IServiceProvider
from flask import Flask
from flask_cors import CORS

sys.path.append(os.getcwd())

from application.infrastructure.utils import get_attributes_ending_with
from framework.merchant_api.infrastructure.middleware import MIDDLEWARE
from framework.merchant_api.infrastructure.service_collection_builder import \
    ServiceCollectionBuilder
from framework.merchant_api.routes.health_router import HEALTH_ROUTER
from framework.merchant_api.routes.merchant_router import MERCHANT_ROUTER
from framework.merchant_api.routes.product_router import PRODUCT_ROUTER
from framework.merchant_api.services.iconfiguration_provider import \
    IConfigurationProvider


async def startup():
    _App = Flask(__name__)

    _ServiceProvider: IServiceProvider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()).build_service_provider()
    _App.service_provider = _ServiceProvider
    _ConfigurationProvider: IConfigurationProvider = _ServiceProvider.get_service(IConfigurationProvider)

    WEB_APP_HOST = _ConfigurationProvider.get_web_app_host()
    WEB_APP_PORT = _ConfigurationProvider.get_web_app_port()

    CORS(_App, resources={r'/api/*': {'origins': f'http://{WEB_APP_HOST}:{WEB_APP_PORT}', "allow_headers": ["*", "Content-Type"]}})

    register_routers(_App)
    register_api_infrastructure(_App)

    _App.run(
        _ConfigurationProvider.get_api_host(),
        _ConfigurationProvider.get_api_port(),
        _ConfigurationProvider.is_debug_mode_enabled(),
        use_reloader = _ConfigurationProvider.is_reloader_enabled()
    )


def register_routers(app: Flask):
    for _Router in get_attributes_ending_with('router', Path() / 'framework' / 'merchant_api' / 'routes'):
        app.register_blueprint(_Router)


def register_api_infrastructure(app: Flask):
    app.register_blueprint(MIDDLEWARE)


if __name__ == '__main__':
    asyncio.run(startup())
