import json
import logging
import os
from pathlib import Path

from pydantic import BaseModel

from dora_api.infrastructure.profile import (Profile, current_profile,
                                             is_production)
from merchant_api.domain.entities.merchant import Merchant
from merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant


_MAPI_PROFILE_DEFAULTS = {
    Profile.DEVELOPMENT: {"log_level": "INFO", "debug": True,
                          # capacitor:// + http://localhost included
                          # so the mobile client (Capacitor) talks to
                          # the dev merchant_api without CORS surgery.
                          "cors_origins": ["http://localhost:5174",
                                           "http://127.0.0.1:5174",
                                           "http://172.17.0.1:5174",
                                           "capacitor://localhost",
                                           "ionic://localhost",
                                           "http://localhost"]},
    Profile.PRODUCTION:  {"log_level": "INFO", "debug": False,
                          "cors_origins": []},
    Profile.TEST:        {"log_level": "WARNING", "debug": True,
                          "cors_origins": ["http://localhost:5174"]},
}


def _env(name: str, default: str | None = None) -> str | None:
    """Resolve an env var, treating empty strings as unset."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class Config(BaseModel):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 5172
    IGA_STORE_ID: int = 52511
    LOG_LEVEL: str = "ERROR"
    MERCHANTS: dict[str, bool] = {
        SupportedMerchant.ALDI.value: True,
        SupportedMerchant.COLES.value: True,
        SupportedMerchant.IGA.value: True,
        SupportedMerchant.WOOLWORTHS.value: True
    }
    WEB_APP_HOST: str = "0.0.0.0"
    WEB_APP_PORT: int = 5174


def _resolve_mapi_config_path() -> Path:
    """D3: appsettings.json lives under <DATA_DIR>/config/ so it
    rides the data volume. Legacy `./config/mapi.appsettings.json`
    is migrated by path_migration.migrate_legacy_appsettings()."""
    data_dir = _env("MAPI_DATA_DIR") or _env("DORA_DATA_DIR", "data")
    return (Path(data_dir).expanduser().resolve()) / "config" / "mapi.appsettings.json"


class ConfigurationManager:
    _config: Config
    _config_path: Path

    def __init__(self):
        self._config_path = _resolve_mapi_config_path()
        try:
            from merchant_api.infrastructure.path_migration import \
                migrate_legacy_appsettings
            migrate_legacy_appsettings(self._config_path)
        except Exception:
            pass

        if not Path.exists(self._config_path):
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, 'w') as _AppSettings:
                _AppSettings.write(Config().model_dump_json(indent = 4))

        with open(self._config_path, 'r') as _AppSettings:
            self._config = Config(**json.load(_AppSettings))

    def get_profile(self) -> Profile:
        return current_profile()

    def get_all_merchants(self) -> list[Merchant]:
        return [
            Merchant(is_enabled = _IsEnabled, name = SupportedMerchant(_MerchantName))
            for _MerchantName, _IsEnabled
            in self._config.MERCHANTS.items()
        ]

    # ── Env-var-first getters ─────────────────────────────────────────
    # MAPI_* env vars take precedence over the JSON appsettings so
    # containerised deployments can override without editing baked-in
    # files. JSON file is still the dev default + source of truth for
    # anything not overridden.

    def get_api_host(self) -> str:
        return _env("MAPI_API_HOST", self._config.API_HOST) or self._config.API_HOST

    def get_api_port(self) -> int:
        return _env_int("MAPI_API_PORT", self._config.API_PORT)

    def get_iga_store_id(self) -> int:
        return _env_int("MAPI_IGA_STORE_ID", self._config.IGA_STORE_ID)

    def get_cors_origins(self) -> list[str]:
        """MAPI_CORS_ORIGINS wins; falls back to DORA_CORS_ORIGINS
        (both APIs typically pinned to the same SPA host) or the
        profile default."""
        raw = _env("MAPI_CORS_ORIGINS") or _env("DORA_CORS_ORIGINS")
        if raw:
            return [o.strip() for o in raw.split(",") if o.strip()]
        return list(_MAPI_PROFILE_DEFAULTS[current_profile()]["cors_origins"])

    def get_log_level(self) -> int:
        env_value = _env("MAPI_LOG_LEVEL")
        json_value = self._config.LOG_LEVEL
        profile_default = _MAPI_PROFILE_DEFAULTS[current_profile()]["log_level"]
        if env_value:
            _LogLevel = env_value.upper()
        elif json_value and json_value != "ERROR":
            _LogLevel = json_value.upper()
        else:
            _LogLevel = profile_default

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
        return _env("DORA_WEB_APP_HOST", self._config.WEB_APP_HOST) or self._config.WEB_APP_HOST

    def get_web_app_port(self) -> int:
        return _env_int("DORA_WEB_APP_PORT", self._config.WEB_APP_PORT)

    def get_data_dir(self) -> Path:
        """Persistent runtime data shared with the dora_api process
        when they run in the same container. Defaults to `./data`."""
        path = _env("MAPI_DATA_DIR") or _env("DORA_DATA_DIR", "data")
        resolved = Path(path).expanduser().resolve()  # type: ignore[arg-type]
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def get_log_dir(self) -> Path:
        """Where logging_setup.py drops rotated log files. Defaults
        to `<DATA_DIR>/logs/mapi`."""
        path = _env("MAPI_LOG_DIR")
        if path:
            resolved = Path(path).expanduser().resolve()
        else:
            resolved = self.get_data_dir() / "logs" / "mapi"
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def get_cache_dir(self) -> Path:
        """Scraped-json + image cache. Defaults to `./cache` for dev;
        `/app/cache` in container. Shared with dora_api via
        DORA_CACHE_DIR when MAPI_CACHE_DIR isn't set."""
        path = _env("MAPI_CACHE_DIR") or _env("DORA_CACHE_DIR", "cache")
        resolved = Path(path).expanduser().resolve()  # type: ignore[arg-type]
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def get_image_cache_dir(self) -> Path:
        """Sub-dir of cache for downloaded product images. Created
        lazily so old-style `.image_cache` in the repo root can be
        migrated here on first boot (see infrastructure/path_migration.py)."""
        path = self.get_cache_dir() / "images"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def is_debug_mode_enabled(self) -> bool:
        raw = _env("MAPI_DEBUG")
        if raw is not None:
            return raw.lower() in {"1", "true", "yes", "on"}
        return bool(_MAPI_PROFILE_DEFAULTS[current_profile()]["debug"])

    def is_reloader_enabled(self) -> bool:
        return False

    def toggle_merchant_enabled_state(self, merchant_name: str) -> None:
        self._config.MERCHANTS[merchant_name] = not self._config.MERCHANTS[merchant_name]
        self._save_configuration()

    def _save_configuration(self) -> None:
        with open(self._config_path, 'w') as _AppSettings:
            _AppSettings.write(self._config.model_dump_json(indent = 4))


CONFIGURATION_MANAGER = ConfigurationManager()  # ensure there is only one instance
