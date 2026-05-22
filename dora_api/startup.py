import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from flask_cors import CORS
from flask_migrate import upgrade

from dora_api.app import app, db
from dora_api.infrastructure.api_response import internal_server_error
from dora_api.infrastructure.configuration_manager import DORA_CONFIG
from dora_api.infrastructure.middleware import MIDDLEWARE
from dora_api.infrastructure.service_wiring import build_dependency_container
from dora_api.infrastructure.utils import get_attributes_ending_with
from dora_api.persistence.seed import seed_dev_data


def startup(is_test_env: bool = False):
    _Container = build_dependency_container()
    app.container = _Container  # type: ignore

    WEB_APP_HOST = DORA_CONFIG.get_web_app_host()
    WEB_APP_PORT = DORA_CONFIG.get_web_app_port()
    # supports_credentials must be True for the browser to send the
    # `dora_session` cookie cross-origin. Origins must be an explicit list
    # (never '*') when credentials are enabled — the browser refuses the
    # wildcard in that case.
    CORS(
        app,
        resources={r'/api/*': {
            'origins': [
                f'http://{WEB_APP_HOST}:{WEB_APP_PORT}',
                f'http://127.0.0.1:{WEB_APP_PORT}',
                f'http://localhost:{WEB_APP_PORT}',
                f'http://172.17.0.1:{WEB_APP_PORT}',
            ],
            'allow_headers': ['Content-Type', 'X-Request-Id'],
            'supports_credentials': True,
        }},
    )

    init_db(is_test_env)
    configure_logger(DORA_CONFIG.get_log_level())
    register_routers()

    if not is_test_env:  # app.run blocks the thread where tests are ran from
        app.run(
            DORA_CONFIG.get_api_host(),
            DORA_CONFIG.get_api_port(),
            DORA_CONFIG.is_debug_mode_enabled(),
            use_reloader = DORA_CONFIG.is_reloader_enabled()
        )


def init_db(is_test_env: bool):
    with app.app_context():
        _AllowDestructive = os.environ.get("DORA_ALLOW_DESTRUCTIVE", "").lower() == "true"

        if is_test_env or (DORA_CONFIG.is_debug_mode_enabled() and _AllowDestructive):
            db.drop_all()
            db.create_all()
            seed_dev_data()
            return

        if DORA_CONFIG.is_debug_mode_enabled():
            # Create any missing tables for local dev, but never drop existing data.
            # Set DORA_ALLOW_DESTRUCTIVE=true to wipe and re-seed.
            db.create_all()
            return

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
