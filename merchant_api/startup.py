import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask
from flask_cors import CORS

from dora_api.infrastructure.utils import get_attributes_ending_with
from merchant_api.infrastructure.configuration_manager import CONFIGURATION_MANAGER
from merchant_api.infrastructure.merchant_data_providers import MERCHANT_DATA_PROVIDERS
from merchant_api.infrastructure.middleware import MIDDLEWARE


def startup():
    _App = Flask(__name__)

    WEB_APP_HOST = CONFIGURATION_MANAGER.get_web_app_host()
    WEB_APP_PORT = CONFIGURATION_MANAGER.get_web_app_port()

    # The web client uses axios `withCredentials: true` for every request
    # (shared with the dora_api so the session cookie rides along), so the
    # merchant_api must also reply with Access-Control-Allow-Credentials: true.
    # Without supports_credentials=True the browser blocks the response and
    # the product-search page fails instantly on first call. Origins must
    # be an explicit list — wildcard origins are forbidden when credentials
    # are enabled.
    CORS(_App, resources={r'/api/*': {
        'origins': [
            f'http://{WEB_APP_HOST}:{WEB_APP_PORT}',
            f'http://127.0.0.1:{WEB_APP_PORT}',
            f'http://localhost:{WEB_APP_PORT}',
            f'http://172.17.0.1:{WEB_APP_PORT}',
        ],
        'allow_headers': ['Content-Type'],
        'supports_credentials': True,
    }})

    configure_logger(CONFIGURATION_MANAGER.get_log_level())
    register_routers(_App)

    scheduler = BackgroundScheduler()
    scheduler.add_job(data_provider_cron_health_check, IntervalTrigger(days = 1))
    scheduler.start()

    _App.run(
        CONFIGURATION_MANAGER.get_api_host(),
        CONFIGURATION_MANAGER.get_api_port(),
        CONFIGURATION_MANAGER.is_debug_mode_enabled(),
        use_reloader = CONFIGURATION_MANAGER.is_reloader_enabled()
    )


def configure_logger(log_level: int):
    _LogFolder = Path() / 'data' / 'logs' / 'mapi'
    Path.mkdir(_LogFolder, parents=True, exist_ok=True)

    _Logger = logging.getLogger()
    _LogFilename = _LogFolder / 'log.txt'
    _FileHandler = TimedRotatingFileHandler(_LogFilename, when="midnight", interval=1, backupCount=30)
    _FileHandler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(lineno)04d | %(message)s'))
    _Logger.setLevel(log_level)
    _Logger.addHandler(_FileHandler)


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
