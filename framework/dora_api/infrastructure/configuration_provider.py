import json
import os
from pathlib import Path

from pydantic import BaseModel

from framework.dora_api.services.iconfiguration_provider import \
    IConfigurationProvider


class ApiKeys(BaseModel):
    GROCY: str


class AppPasswords(BaseModel):
    GOOGLE: str


class Emails(BaseModel):
    BEN: str
    SENDER: str


class Urls(BaseModel):
    GROCY: str


class Config(BaseModel):
    API_HOST: str
    API_KEYS: ApiKeys
    API_PORT: int
    APP_PASSWORDS: AppPasswords
    DEBUG: bool
    EMAILS: Emails
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool
    URLS: Urls
    USE_RELOADER: bool
    WEB_APP_HOST: str
    WEB_APP_PORT: int


class ConfigurationProvider(IConfigurationProvider):
    _configuration: Config

    def __init__(self):
        basedir = Path(__file__).parent.parent
        with open(os.path.join(basedir, 'appsettings.json'), 'r') as _AppSettings:
            self._configuration = Config(**json.load(_AppSettings))

    def get_api_host(self) -> str:
        return self._configuration.API_HOST

    def get_api_port(self) -> int:
        return self._configuration.API_PORT

    def get_db_connection_string(self) -> str:
        return self._configuration.SQLALCHEMY_DATABASE_URI

    def get_web_app_host(self) -> str:
        return self._configuration.WEB_APP_HOST

    def get_web_app_port(self) -> int:
        return self._configuration.WEB_APP_PORT

    def is_debug_mode_enabled(self) -> bool:
        return self._configuration.DEBUG

    def is_modification_tracking_enabled(self) -> bool:
        return self._configuration.SQLALCHEMY_TRACK_MODIFICATIONS

    def is_reloader_enabled(self) -> bool:
        return self._configuration.USE_RELOADER

