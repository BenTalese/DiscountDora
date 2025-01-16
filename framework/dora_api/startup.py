import asyncio
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from clapy import DependencyInjectorServiceProvider, IServiceProvider
from flask_cors import CORS
from flask_migrate import Migrate, upgrade

sys.path.append(os.getcwd())

from application.infrastructure.utils import get_attributes_ending_with
from framework.dora_api.app import app, db
from framework.dora_api.infrastructure.error_handlers import ERROR_HANDLERS
from framework.dora_api.infrastructure.middleware import MIDDLEWARE
from framework.dora_api.infrastructure.service_collection_builder import \
    ServiceCollectionBuilder
from framework.dora_api.persistence.persistence_context import \
    SqlAlchemyPersistenceContext
from framework.dora_api.persistence.persistence_helper_methods import \
    verify_all_models_imported
from framework.dora_api.persistence.seed import (seed_dev_data_async,
                                                 seed_system_data_async)
from framework.dora_api.services.iconfiguration_manager import \
    IConfigurationManager


async def startup():
    _ServiceProvider: IServiceProvider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()).build_service_provider()
    app.service_provider = _ServiceProvider
    _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)

    await init_db()

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

    app.run(
        _ConfigurationManager.get_api_host(),
        _ConfigurationManager.get_api_port(),
        _ConfigurationManager.is_debug_mode_enabled(),
        use_reloader = _ConfigurationManager.is_reloader_enabled()
    )


async def init_db():
    verify_all_models_imported()
    import framework.dora_api.persistence.models  # Makes models visible to db instance  # noqa: F401
    db.init_app(app)
    Migrate(app, db, Path(__file__).parent / 'persistence' / 'migrations')

    SqlAlchemyPersistenceContext._flask_app = app
    SqlAlchemyPersistenceContext._model_classes = {
        mapper.class_.__entity__: mapper.class_
        for mapper in db.Model.registry.mappers
    }

    with app.app_context():
        if app.config.get('DEBUG'):
            db.drop_all()
            db.create_all()
            await seed_dev_data_async(SqlAlchemyPersistenceContext())
            await seed_system_data_async(SqlAlchemyPersistenceContext())
        else:
            upgrade()
            # TODO: Move to migration script
            await seed_system_data_async(SqlAlchemyPersistenceContext())


def configure_logger(log_level: int):
    _LogFolder = Path() / 'logs' / 'dora_api'
    if not Path.exists(_LogFolder):
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
