import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from flask_cors import CORS
from flask_migrate import upgrade

from dora_api.app import app, db
from dora_api.infrastructure.api_response import internal_server_error
from dora_api.infrastructure.configuration_manager import DoraConfig
from dora_api.infrastructure.middleware import MIDDLEWARE
from dora_api.infrastructure.service_wiring import build_dependency_container
from dora_api.infrastructure.utils import get_attributes_ending_with
from dora_api.persistence.seed import seed_dev_data
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


def startup(is_test_env: bool = False):
    _Container = build_dependency_container()
    app.container = _Container  # type: ignore
    _Config = DoraConfig()

    WEB_APP_HOST = _Config.get_web_app_host()
    WEB_APP_PORT = _Config.get_web_app_port()
    CORS(app, resources={r'/api/*': {'origins': [
        f'http://{WEB_APP_HOST}:{WEB_APP_PORT}',
        f'http://127.0.0.1:{WEB_APP_PORT}',
        f'http://localhost:{WEB_APP_PORT}',
        f'http://172.17.0.1:{WEB_APP_PORT}',
    ], 'allow_headers': ['*', 'Content-Type']}})

    init_db(_Config, is_test_env)
    configure_logger(_Config.get_log_level())
    register_routers()

    if not is_test_env:  # app.run blocks the thread where tests are ran from
        app.run(
            _Config.get_api_host(),
            _Config.get_api_port(),
            _Config.is_debug_mode_enabled(),
            use_reloader = _Config.is_reloader_enabled()
        )


def init_db(config: DoraConfig, is_test_env: bool):
    SqlAlchemyRepository._flask_app = app
    with app.app_context():
        if config.is_debug_mode_enabled() or is_test_env:
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
    app.register_blueprint(MIDDLEWARE)


@app.errorhandler(Exception)
def handle_global_exception(error: Exception):
    logging.getLogger().exception("Unhandled exception", exc_info=error)
    return internal_server_error("An unexpected error occurred.")


if __name__ == '__main__':
    startup()
