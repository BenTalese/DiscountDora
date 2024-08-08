import json
import logging
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel

from framework.merchant_api.domain.entities.merchant import Merchant
from framework.merchant_api.domain.enumerations.supported_merchant import SupportedMerchant
from framework.merchant_api.services.iconfiguration_manager import \
    IConfigurationManager


class Config(BaseModel):
    API_HOST: str = "localhost"
    API_PORT: int = 5172
    IGA_STORE_ID: int = 52511
    LOG_LEVEL: str = "ERROR"
    MERCHANTS: Dict[str, bool] = {
        SupportedMerchant.ALDI.value: True,
        SupportedMerchant.COLES.value: True,
        SupportedMerchant.IGA.value: True,
        SupportedMerchant.WOOLWORTHS.value: True
    }
    USE_DEBUG_MODE: bool = True
    USE_RELOADER: bool = False
    WEB_APP_HOST: str = "localhost"
    WEB_APP_PORT: int = 5174


class ConfigurationManager(IConfigurationManager):
    _config: Config
    _config_path: str = Path(__file__).parent.parent / 'appsettings.json'

    def __init__(self):
        if not Path.exists(self._config_path):
            with open(self._config_path, 'w') as _AppSettings:
                _AppSettings.write(Config().model_dump_json(indent = 4))

        with open(self._config_path, 'r') as _AppSettings:
            self._config = Config(**json.load(_AppSettings))

    def get_all_merchants(self) -> List[Merchant]:
        return [
            Merchant(is_enabled = _IsEnabled, name = SupportedMerchant(_MerchantName))
            for _MerchantName, _IsEnabled
            in self._config.MERCHANTS.items()
        ]

    def get_api_host(self) -> str:
        return self._config.API_HOST

    def get_api_port(self) -> int:
        return self._config.API_PORT

    def get_iga_store_id(self) -> int:
        return self._config.IGA_STORE_ID

    def get_log_level(self) -> int:
        _LogLevel = self._config.LOG_LEVEL

        if _LogLevel == "INFO":
            return logging.INFO

        if _LogLevel == "DEBUG":
            return logging.DEBUG

        if _LogLevel == "WARNING":
            return logging.WARNING

        if _LogLevel == "ERROR":
            return logging.ERROR

        if _LogLevel == "CRITICAL":
            return logging.CRITICAL

        if _LogLevel == "FATAL":
            return logging.FATAL

        return logging.NOTSET

    def get_web_app_host(self) -> str:
        return self._config.WEB_APP_HOST

    def get_web_app_port(self) -> int:
        return self._config.WEB_APP_PORT

    def is_debug_mode_enabled(self) -> bool:
        return self._config.USE_DEBUG_MODE

    def is_reloader_enabled(self) -> bool:
        return self._config.USE_RELOADER

    def toggle_merchant_enabled_state(self, merchant_name: str) -> None:
        self._config.MERCHANTS[merchant_name] = not self._config.MERCHANTS[merchant_name]
        self._save_configuration()

    def _save_configuration(self) -> None:
        with open(self._config_path, 'w') as _AppSettings:
            json.dump(self._config.model_dump_json(), _AppSettings, indent = 4)
