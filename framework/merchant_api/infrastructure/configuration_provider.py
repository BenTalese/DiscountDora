import json
import os
from pathlib import Path

from pydantic import BaseModel

from framework.merchant_api.services.iconfiguration_provider import \
    IConfigurationProvider


class Config(BaseModel):
    API_HOST: str
    API_PORT: int
    CHROMEDRIVER_PATH: str
    DEBUG: bool
    IGA_STORE_ID: int
    USE_RELOADER: bool
    WEB_APP_HOST: str
    WEB_APP_PORT: int


class ConfigurationProvider(IConfigurationProvider):
    _configuration: Config

    def __init__(self):
        _Path = Path(__file__).parent.parent / 'appsettings.json'
        with open(_Path, 'r') as _AppSettings:
            self._configuration = Config(**json.load(_AppSettings))

    def get_api_host(self) -> str:
        return self._configuration.API_HOST

    def get_api_port(self) -> int:
        return self._configuration.API_PORT

    def get_web_app_host(self) -> str:
        return self._configuration.WEB_APP_HOST

    def get_web_app_port(self) -> int:
        return self._configuration.WEB_APP_PORT

    def is_debug_mode_enabled(self) -> bool:
        return self._configuration.DEBUG

    def is_reloader_enabled(self) -> bool:
        return self._configuration.USE_RELOADER

