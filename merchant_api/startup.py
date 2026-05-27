import logging
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask
from flask_cors import CORS

from dora_api.infrastructure.logging_setup import configure_logging
from dora_api.infrastructure.utils import get_attributes_ending_with
from merchant_api.infrastructure.configuration_manager import CONFIGURATION_MANAGER
from merchant_api.infrastructure.merchant_data_providers import MERCHANT_DATA_PROVIDERS
from merchant_api.infrastructure.middleware import MIDDLEWARE


def build_app() -> Flask:
    """Construct + wire the merchant Flask app, but DO NOT run it.

    Split from `startup()` so the desktop bundle can embed the same
    app object inside its own thread via `werkzeug.serving.make_server`,
    without having merchant_api take control of process lifecycle.
    Idempotent on side effects (CORS, blueprints, scheduler) — calling
    twice would double-register them, so don't.
    """
    # D3: refuse to boot in production without the required env vars.
    # Shares the same gate as dora_api so a misconfigured deploy fails
    # the same way regardless of which container starts first. The
    # desktop bundle sets DORA_SKIP_PROD_VALIDATION=true so this is a
    # no-op there.
    from dora_api.infrastructure.profile import \
        validate_production_requirements
    validate_production_requirements()

    _App = Flask(__name__)

    # D3: profile-aware CORS pinning, same pattern as dora_api. The
    # web client uses `withCredentials: true` so the cross-origin
    # session cookie rides along — origins MUST be an explicit list
    # (never '*') when credentials are enabled.
    CORS(_App, resources={r'/api/*': {
        'origins': CONFIGURATION_MANAGER.get_cors_origins(),
        'allow_headers': ['Content-Type', 'X-Request-Id'],
        'supports_credentials': True,
    }})

    # D2: migrate the repo-root .image_cache (and seed the aldi
    # categories file) before any provider boots and reaches for
    # them.
    from merchant_api.infrastructure.path_migration import \
        migrate_legacy_image_cache
    migrate_legacy_image_cache(CONFIGURATION_MANAGER.get_cache_dir())

    configure_logging(
        "mapi",
        CONFIGURATION_MANAGER.get_log_dir(),
        debug=CONFIGURATION_MANAGER.is_debug_mode_enabled(),
    )
    register_routers(_App)

    scheduler = BackgroundScheduler()
    scheduler.add_job(data_provider_cron_health_check, IntervalTrigger(days = 1))
    scheduler.start()

    return _App


def startup():
    """Stand-alone runner: builds the Flask app and calls .run().
    Used by `python -m merchant_api.startup` and by startup.sh in
    the Docker container."""
    _App = build_app()
    _App.run(
        CONFIGURATION_MANAGER.get_api_host(),
        CONFIGURATION_MANAGER.get_api_port(),
        CONFIGURATION_MANAGER.is_debug_mode_enabled(),
        use_reloader = CONFIGURATION_MANAGER.is_reloader_enabled()
    )


def register_routers(app: Flask):
    for _Router in get_attributes_ending_with('router', Path() / 'merchant_api' / 'features'):
        app.register_blueprint(_Router)
    app.register_blueprint(MIDDLEWARE)


def data_provider_cron_health_check():
    _Logger = logging.getLogger(__name__)
    _Merchants = CONFIGURATION_MANAGER.get_all_merchants()
    _Logger.info("Running health check for merchant data providers.")

    for _MerchantDataProvider in MERCHANT_DATA_PROVIDERS:

        try:
            _Offers = _MerchantDataProvider.search_by_term(
                'Chocolate Ice Cream',
                next(_Merchant for _Merchant in _Merchants if _MerchantDataProvider.is_merchant_supported(_Merchant)),
                1)

            _MerchantDataProvider.is_healthy = bool(_Offers)
            _Log = f"Merchant Data Provider '{_MerchantDataProvider.base_url}' is {'HEALTHY' if _MerchantDataProvider.is_healthy else 'NOT HEALTHY'}."
            _Logger.info(_Log) if _MerchantDataProvider.is_healthy else _Logger.warning(_Log)

        except Exception:
            _MerchantDataProvider.is_healthy = False
            _Logger.exception(f"Merchant data provider '{_MerchantDataProvider.base_url}' encountered a problem during health check.")


if __name__ == '__main__':
    startup()
