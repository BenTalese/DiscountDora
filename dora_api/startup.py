import logging
import os
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask_cors import CORS
from flask_migrate import upgrade

from dora_api.app import app, db
from dora_api.infrastructure.api_response import internal_server_error
from dora_api.infrastructure.audit_retention import prune_audit_events
from dora_api.infrastructure.configuration_manager import DORA_CONFIG
from dora_api.infrastructure.logging_setup import configure_logging
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
    configure_logging(
        "dapi",
        Path().resolve() / "data" / "logs" / "dapi",
        debug=DORA_CONFIG.is_debug_mode_enabled(),
    )
    register_routers()

    if not is_test_env:
        # Nightly audit-log retention sweep. Hour 3 local time keeps it
        # well clear of any deals-email schedule. Tests skip the
        # scheduler entirely — they don't run long enough to trip it,
        # and we don't want a background thread surviving the test
        # session.
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            prune_audit_events,
            CronTrigger(hour=3, minute=0),
            id="audit_retention",
            replace_existing=True,
        )
        scheduler.start()

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
