import json
import logging
from pathlib import Path

from pydantic import BaseModel

from framework.dora_api.services.iconfiguration_manager import \
    IConfigurationManager


class Config(BaseModel):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 5170
    LOG_LEVEL: str = "ERROR"
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{Path().resolve() / 'data' / 'dora.data.db'}"
    WEB_APP_HOST: str = "0.0.0.0"
    WEB_APP_PORT: int = 5174


class ConfigurationManager(IConfigurationManager):
    _config: Config
    _config_path: Path = Path() / 'config' / 'dapi.appsettings.json'

    def __init__(self):
        if not Path.exists(self._config_path):
            with open(self._config_path, 'w') as _AppSettings:
                _AppSettings.write(Config().model_dump_json(indent = 4))

        with open(self._config_path, 'r') as _AppSettings:
            self._config = Config(**json.load(_AppSettings))

    def get_api_host(self) -> str:
        return self._config.API_HOST

    def get_api_port(self) -> int:
        return self._config.API_PORT

    def get_db_connection_string(self) -> str:
        return self._config.SQLALCHEMY_DATABASE_URI

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
        return False

    def is_modification_tracking_enabled(self) -> bool:
        return True

    def is_reloader_enabled(self) -> bool:
        return False

    def _save_configuration(self) -> None:
        with open(self._config_path, 'w') as _AppSettings:
            json.dump(self._config.model_dump_json(), _AppSettings, indent = 4)
