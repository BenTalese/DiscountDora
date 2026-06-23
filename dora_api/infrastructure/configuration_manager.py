import json
import logging
import os
from pathlib import Path

from pydantic import BaseModel

from dora_api.infrastructure.profile import (Profile, current_profile,
                                             is_production, is_test)


class Config(BaseModel):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 5170
    LOG_LEVEL: str = "ERROR"
    WEB_APP_HOST: str = "0.0.0.0"
    WEB_APP_PORT: int = 5174


# D3: per-profile defaults for things that meaningfully differ between
# dev and prod. The JSON appsettings still wins when an operator pins
# a value there, and env vars still win over JSON — these are just the
# "what should it be when nothing's pinned" fallbacks.
_PROFILE_DEFAULTS = {
    Profile.DEVELOPMENT: {
        "log_level": "DEBUG",
        "debug": True,
        # Dev SPA runs on localhost ports; permissive list to cover
        # `quasar dev` (5174) and the various ways a browser might
        # reach it on a dev machine. The `capacitor://localhost` /
        # `http://localhost` origins are for the Capacitor mobile
        # client (Quasar `-m capacitor`) talking to a dev backend on
        # the same machine; iOS uses `capacitor://`, Android uses
        # `http://localhost`. Pin via DORA_CORS_ORIGINS in prod.
        "cors_origins": [
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://172.17.0.1:5174",
            "capacitor://localhost",
            "ionic://localhost",
            "http://localhost",
        ],
    },
    Profile.PRODUCTION: {
        "log_level": "INFO",
        "debug": False,
        # No safe default for prod CORS — has to be pinned via
        # DORA_CORS_ORIGINS (the production-requirements check refuses
        # to boot without it).
        "cors_origins": [],
    },
    Profile.TEST: {
        "log_level": "WARNING",
        "debug": True,
        "cors_origins": ["http://localhost:5174"],
    },
}


def _env(name: str, default: str | None = None) -> str | None:
    """Resolve an env var, treating empty strings as unset so an
    accidental `DORA_API_PORT=` in .env doesn't blow up int parsing."""
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


def _resolve_db_path() -> Path:
    """DORA_DB_PATH wins when set (absolute or relative); otherwise
    fall back to `<DORA_DATA_DIR or 'data'>/dora.data.db`. The two-tier
    layout means deployments can either pin the file directly or just
    tell the app where its data directory lives."""
    explicit = _env("DORA_DB_PATH")
    if explicit:
        return Path(explicit).expanduser().resolve()
    data_dir = _env("DORA_DATA_DIR", "data")
    return (Path(data_dir).expanduser().resolve()) / "dora.data.db"


def _resolve_config_path() -> Path:
    """D3: appsettings.json lives under <DATA_DIR>/config/ so the
    operator's persistent overrides ride the data volume. The legacy
    `./config/dapi.appsettings.json` location is migrated by
    path_migration.migrate_legacy_appsettings() on startup."""
    data_dir = _env("DORA_DATA_DIR", "data")
    return (Path(data_dir).expanduser().resolve()) / "config" / "dapi.appsettings.json"


class DoraConfig:
    _config: Config
    _config_path: Path

    def __init__(self):
        self._config_path = _resolve_config_path()
        # D3: relocated to <DATA_DIR>/config/. Attempt to move a
        # legacy ./config/dapi.appsettings.json into the new home so
        # operators that customised it don't silently lose their
        # tweaks. Must happen before the file-exists check so the
        # generated-defaults branch doesn't overwrite the moved file.
        try:
            from dora_api.infrastructure.path_migration import \
                migrate_legacy_appsettings
            migrate_legacy_appsettings(self._config_path)
        except Exception:
            # Migration is best-effort — never block startup over it.
            pass

        if not Path.exists(self._config_path):
            # D3: generate sensible defaults on first boot. Operators
            # can edit afterwards; env vars still win.
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, 'w') as _AppSettings:
                _AppSettings.write(Config().model_dump_json(indent = 4))

        with open(self._config_path, 'r') as _AppSettings:
            self._config = Config(**json.load(_AppSettings))

    def get_profile(self) -> Profile:
        return current_profile()

    # ── Env-var-first getters ─────────────────────────────────────────
    # Every getter reads the relevant env var first and falls back to
    # the JSON appsettings value. The JSON file is still the source of
    # truth for un-overridden values + dev defaults, but containerised
    # deployments can override any of these via .env without editing
    # files in the image.

    def get_api_host(self) -> str:
        return _env("DORA_API_HOST", self._config.API_HOST) or self._config.API_HOST

    def get_api_port(self) -> int:
        return _env_int("DORA_API_PORT", self._config.API_PORT)

    def get_db_connection_string(self) -> str:
        path = _resolve_db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"

    def get_log_level(self) -> int:
        # D3: layered resolution — env > JSON > profile default. JSON
        # default is "ERROR" (legacy); when the JSON has the legacy
        # value we treat it as "use the profile default" so dev
        # actually gets DEBUG logs without an explicit override.
        env_value = _env("DORA_LOG_LEVEL")
        json_value = self._config.LOG_LEVEL
        profile_default = _PROFILE_DEFAULTS[current_profile()]["log_level"]
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

    def get_cors_origins(self) -> list[str]:
        """Comma-separated list from DORA_CORS_ORIGINS; falls back to
        the profile default. Production has no fallback — the env var
        must be set (validated by validate_production_requirements())."""
        raw = _env("DORA_CORS_ORIGINS")
        if raw:
            return [o.strip() for o in raw.split(",") if o.strip()]
        return list(_PROFILE_DEFAULTS[current_profile()]["cors_origins"])

    def is_seed_allowed(self) -> bool:
        """Dev seed only runs in development; production refuses
        regardless of DORA_ALLOW_DESTRUCTIVE."""
        if is_production():
            return False
        return _env("DORA_ALLOW_DESTRUCTIVE", "false").lower() in {"1", "true", "yes", "on"}

    def get_web_app_host(self) -> str:
        return _env("DORA_WEB_APP_HOST", self._config.WEB_APP_HOST) or self._config.WEB_APP_HOST

    def get_web_app_port(self) -> int:
        return _env_int("DORA_WEB_APP_PORT", self._config.WEB_APP_PORT)

    def get_data_dir(self) -> Path:
        """Persistent runtime data — sqlite db, secret_key, staged
        uploads. Defaults to `./data` for dev; `/app/data` in container."""
        path = _env("DORA_DATA_DIR", "data")
        resolved = Path(path).expanduser().resolve()  # type: ignore[arg-type]
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def get_uploads_dir(self) -> Path:
        """Chunked uploads staged here before being inspected /
        committed. Lives under the data dir so backups capture
        in-flight uploads too. Stale entries swept by the uploads
        feature."""
        path = self.get_data_dir() / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_voices_dir(self) -> Path:
        """Where Piper TTS voice models (`.onnx` + `.onnx.json`) are stored.
        Downloaded on demand from the catalog (see features/tts) into the data
        dir so they persist across restarts (captured by backups, ride a
        mounted volume) and never bloat the repo. `DORA_PIPER_VOICE_DIR`
        overrides the location for operators who stage models elsewhere."""
        override = _env("DORA_PIPER_VOICE_DIR")
        if override:
            path = Path(override).expanduser().resolve()
        else:
            path = self.get_data_dir() / "voices"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_log_dir(self) -> Path:
        """Where logging_setup.py drops rotated log files. Defaults to
        `<DATA_DIR>/logs/dapi` so logs sit next to other runtime
        state."""
        path = _env("DORA_LOG_DIR")
        if path:
            resolved = Path(path).expanduser().resolve()
        else:
            resolved = self.get_data_dir() / "logs" / "dapi"
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def get_cache_dir(self) -> Path:
        """Image / scraped-data cache dir. Defaults to `./cache` for
        dev; `/app/cache` in container."""
        path = _env("DORA_CACHE_DIR", "cache")
        resolved = Path(path).expanduser().resolve()  # type: ignore[arg-type]
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def is_debug_mode_enabled(self) -> bool:
        # D3: explicit env wins; otherwise pick the profile default.
        raw = _env("DORA_DEBUG")
        if raw is not None:
            return raw.lower() in {"1", "true", "yes", "on"}
        return bool(_PROFILE_DEFAULTS[current_profile()]["debug"])

    def is_modification_tracking_enabled(self) -> bool:
        return True

    def is_reloader_enabled(self) -> bool:
        return False

    def _save_configuration(self) -> None:
        with open(self._config_path, 'w') as _AppSettings:
            _AppSettings.write(self._config.model_dump_json(indent = 4))


DORA_CONFIG = DoraConfig()
