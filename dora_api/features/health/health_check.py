"""GET /api/health — readiness + compatibility probe.

Two callers in mind:
  - Container HEALTHCHECK / monitoring → cares about HTTP 200.
  - Mobile + desktop clients → reading the JSON body to decide
    whether the backend version is compatible with the client
    (`schema_version` lets a thin client refuse to talk to a
    backend that's been migrated past it) and whether features it
    relies on are enabled (e.g. the assistant chat panel hides
    itself when `features.assistant` is false).

Cheap by design: never touches the DB or external services. The
schema version is resolved once at module import.
"""
import logging
import os
from pathlib import Path

from flask import jsonify

from dora_api.features.help.version_info import CURRENT_VERSION
from dora_api.features.routers import HEALTH_ROUTER


def _resolve_schema_head() -> str | None:
    """Read the alembic head revision from the migrations directory.
    Module-load only — schema versions don't change at runtime, and
    we don't want every health probe to hit alembic."""
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        cfg = Config()
        cfg.set_main_option(
            "script_location",
            str(Path(__file__).resolve().parents[2] / "persistence" / "migrations"),
        )
        return ScriptDirectory.from_config(cfg).get_current_head()
    except Exception:
        # Best-effort: if alembic can't introspect (broken metadata,
        # missing script), prefer to keep the health endpoint up and
        # report null rather than failing the probe entirely.
        return None


_SCHEMA_HEAD = _resolve_schema_head()


def _feature_flags() -> dict[str, bool]:
    """Surface what the backend can do, for client capability gating.
    Reads runtime state cheaply — DB-backed flags pull from the
    AppSettings singleton; env-driven flags read the env var directly."""
    flags: dict[str, bool] = {
        "auth": True,           # always — session cookies + login flow
        "audit": True,          # always — audit_log + audit panel
        "barcodes": True,
        "multi_user": True,     # register + admin role
        "email": os.environ.get("DORA_EMAIL_ENABLED", "false").lower()
                 in {"1", "true", "yes", "on"},
        "assistant": False,     # resolved below
    }
    # AppSettings drives the assistant flag at runtime. Wrapped so
    # a DB hiccup doesn't take the health probe down with it.
    try:
        from dora_api.features.app_settings.access import \
            get_or_create_app_settings
        flags["assistant"] = bool(get_or_create_app_settings().llm_enabled)
    except Exception:
        pass
    return flags


@HEALTH_ROUTER.route("")
def health_check():
    """Single endpoint for both monitoring and client compatibility.
    Mobile/desktop clients can rely on the response shape never
    losing keys — we add, but don't remove."""
    logging.getLogger(__name__).info("API health check requested.")
    return jsonify({
        "ok": True,
        "version": CURRENT_VERSION,
        "schema_version": _SCHEMA_HEAD,
        "profile": (os.environ.get("DORA_ENV") or "development").lower(),
        "features": _feature_flags(),
    }), 200
