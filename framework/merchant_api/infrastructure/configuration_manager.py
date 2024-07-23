import json
import logging
from pathlib import Path
from typing import List

from pydantic import BaseModel

from framework.merchant_api.domain.entities.merchant import Merchant
from framework.merchant_api.services.iconfiguration_manager import \
    IConfigurationManager


class Config(BaseModel):
    API_HOST: str
    API_PORT: int
    DEBUG: bool
    IGA_STORE_ID: int
    LOG_LEVEL: str
    MERCHANTS: List[Merchant]
    USE_RELOADER: bool
    WEB_APP_HOST: str
    WEB_APP_PORT: int


class ConfigurationManager(IConfigurationManager):
    _config: Config
    _config_path: str

    def __init__(self):
        # TODO: IF NOT EXISTS, SEED
        self._config_path = Path(__file__).parent.parent / 'appsettings.json'
        with open(self._config_path, 'r') as _AppSettings:
            self._config = Config(**json.load(_AppSettings))

    def get_all_merchants(self) -> List[Merchant]:
        return [_Merchant for _Merchant in self._config.MERCHANTS]

    def get_api_host(self) -> str:
        return self._config.API_HOST

    def get_api_port(self) -> int:
        return self._config.API_PORT

    def get_enabled_merchants(self) -> List[Merchant]:
        return [_Merchant for _Merchant in self._config.MERCHANTS if _Merchant.is_enabled]

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
        return self._config.DEBUG

    def is_reloader_enabled(self) -> bool:
        return self._config.USE_RELOADER

    def set_settings_to_defaults(self) -> None:
        # TODO: IF EXISTS, DELETE
        # TODO: CREATE NEW
        pass

    def toggle_merchant_enabled_state(self, merchant: Merchant) -> None:
        _IndexToUpdate = self._config.MERCHANTS.index(merchant)
        _MerchantToUpdate = self._config.MERCHANTS[_IndexToUpdate]
        _MerchantToUpdate.is_enabled = not _MerchantToUpdate.is_enabled
        self._save_configuration()

    def _save_configuration(self) -> None:
        with open(self._config_path, 'w') as _AppSettings:
            json.dump(self._config.model_dump_json(), _AppSettings, indent = 4)
