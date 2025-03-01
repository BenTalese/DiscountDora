import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from clapy import DependencyInjectorServiceProvider, IServiceProvider
from flask_cors import CORS
from flask_migrate import upgrade

from application.infrastructure.utils import get_attributes_ending_with
from framework.dora_api.app import app, db
from framework.dora_api.infrastructure.configuration_manager import \
    ConfigurationManager
from framework.dora_api.infrastructure.error_handlers import ERROR_HANDLERS
from framework.dora_api.infrastructure.middleware import MIDDLEWARE
from framework.dora_api.infrastructure.service_collection_builder import \
    ServiceCollectionBuilder
from framework.dora_api.persistence.persistence_context import \
    SqlAlchemyPersistenceContext
from framework.dora_api.persistence.persistence_helper_methods import \
    verify_all_models_imported
from framework.dora_api.persistence.seed import seed_dev_data_async
from framework.dora_api.services.iconfiguration_manager import \
    IConfigurationManager


async def startup(is_test_env: bool = False):
    _ServiceProvider: IServiceProvider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()).build_service_provider()
    app.service_provider = _ServiceProvider
    _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)

    await init_db(is_test_env)

    WEB_APP_HOST = _ConfigurationManager.get_web_app_host()
    WEB_APP_PORT = _ConfigurationManager.get_web_app_port()

    CORS(app, resources={r'/api/*': {
        'origins': [
            f'http://{WEB_APP_HOST}:{WEB_APP_PORT}',
            f'http://127.0.0.1:{WEB_APP_PORT}',
            f'http://localhost:{WEB_APP_PORT}',
            f'http://172.17.0.1:{WEB_APP_PORT}'
        ],
        'allow_headers': ['*', 'Content-Type']
    }})

    configure_logger(_ConfigurationManager.get_log_level())
    register_routers()
    register_api_infrastructure()

    if not is_test_env:  # app.run blocks the thread where tests are ran from
        app.run(
            _ConfigurationManager.get_api_host(),
            _ConfigurationManager.get_api_port(),
            _ConfigurationManager.is_debug_mode_enabled(),
            use_reloader = _ConfigurationManager.is_reloader_enabled()
        )


async def init_db(is_test_env: bool = False):
    verify_all_models_imported()

    SqlAlchemyPersistenceContext._flask_app = app
    SqlAlchemyPersistenceContext._model_classes = {
        mapper.class_.__entity__: mapper.class_
        for mapper in db.Model.registry.mappers
    }

    with app.app_context():
        if ConfigurationManager().is_debug_mode_enabled() or is_test_env:
            db.drop_all()
            db.create_all()
            await seed_dev_data_async(SqlAlchemyPersistenceContext())
        else:
            upgrade()


def configure_logger(log_level: int):
    _LogFolder = Path().resolve() / 'data' / 'logs' / 'dapi'
    Path.mkdir(_LogFolder, parents=True, exist_ok=True)

    _Logger = logging.getLogger()
    _LogFilename = _LogFolder / 'log.txt'
    _FileHandler = TimedRotatingFileHandler(_LogFilename, when="midnight", interval=1, backupCount=30)
    _FileHandler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(lineno)04d | %(message)s'))
    _Logger.setLevel(log_level)
    _Logger.addHandler(_FileHandler)


def register_routers():
    for _Router in get_attributes_ending_with('router', Path() / 'framework' / 'dora_api' / 'routes'):
        app.register_blueprint(_Router)


def register_api_infrastructure():
    app.register_blueprint(MIDDLEWARE)
    app.register_blueprint(ERROR_HANDLERS)


if __name__ == '__main__':
    asyncio.run(startup())
