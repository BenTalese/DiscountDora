import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from flask_cors import CORS
from flask_migrate import upgrade

from dora_api.app import app, db
from dora_api.infrastructure.configuration_manager import ConfigurationManager
from dora_api.infrastructure.error_handlers import ERROR_HANDLERS
from dora_api.infrastructure.middleware import MIDDLEWARE
from dora_api.infrastructure.service_wiring import build_dependency_container
from dora_api.infrastructure.utils import get_attributes_ending_with
from dora_api.persistence.seed import seed_dev_data
from dora_api.persistence.sqlalchemy_repository import (
    SqlAlchemyRepository, verify_all_models_imported)
from dora_api.services.iconfiguration_manager import IConfigurationManager


def startup(is_test_env: bool = False):
    _Container = build_dependency_container()
    app.container = _Container  # type: ignore
    _ConfigurationManager = _Container.inject(IConfigurationManager)

    init_db(is_test_env)

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


def init_db(is_test_env: bool = False):
    verify_all_models_imported()

    SqlAlchemyRepository._flask_app = app
    SqlAlchemyRepository._model_classes = {
        mapper.class_.__entity__: mapper.class_
        for mapper in db.Model.registry.mappers  # type: ignore
    }

    with app.app_context():
        if ConfigurationManager().is_debug_mode_enabled() or is_test_env:
            db.drop_all()
            db.create_all()
            seed_dev_data()
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
    for _Router in get_attributes_ending_with('router', Path() / 'dora_api' / 'features'):
        app.register_blueprint(_Router)


def register_api_infrastructure():
    app.register_blueprint(MIDDLEWARE)
    app.register_blueprint(ERROR_HANDLERS)


if __name__ == '__main__':
    startup()
