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
    AppSettings singleton; env-driven flags read the env var directly.

    Key contract: keys never *removed*. New install-wide flags get
    added here whenever C-cross §2.6 grows its admin panel. Per ADR-002,
    every consumer reads the truth through this endpoint, not direct
    AppSetting access on the client.
    """
    flags: dict[str, bool] = {
        "auth": True,           # always — session cookies + login flow
        "audit": True,          # always — audit_log + audit panel
        "scanning": False,      # resolved below — off by default
        "multi_user": True,     # register + admin role
        "email": os.environ.get("DORA_EMAIL_ENABLED", "false").lower()
                 in {"1", "true", "yes", "on"},
        # C-9.7 — derived from `DORA_SMTP_USERNAME` (same check
        # `email_sender._config()` uses for dry-run mode). The SPA reads
        # this to disable channel toggles (R-014 — shown-disabled until
        # the channel is wired); it's distinct from `email` (a coarse
        # install-feature flag) and `deals_email` (the install-wide
        # deals-email feature). True ⇒ transactional sends actually
        # leave the box.
        "email_smtp_configured": bool(
            os.environ.get("DORA_SMTP_USERNAME", "").strip()
        ),
        # C-9.8 — same shape for the web-push channel: True when both
        # VAPID halves (public + private) are set. The SPA reads this
        # to disable the Push toggle in Preferences (R-014); the push
        # sender itself drops to dry-run when either is missing.
        "push_vapid_configured": bool(
            os.environ.get("DORA_VAPID_PUBLIC_KEY", "").strip()
            and os.environ.get("DORA_VAPID_PRIVATE_KEY", "").strip()
        ),
        "assistant": False,     # resolved below
        # C-cross Chunk 1 — install-wide feature flags (proposal §2.6).
        # Each pairs with a per-user opt-in (where one exists) — install
        # off ⇒ feature hidden for everyone; install on ⇒ per-user opt-in
        # still applies. Resolved below from AppSetting.
        "meal_planning": True,
        "money": False,
        "nutrition": False,
        "companion_ingestion": False,
        "deals_email": False,
        # Products is a data-presence overlay (PROPOSAL_PRODUCTS_AS_OVERLAY /
        # FU-209): true iff product data has been ingested — not an admin/user
        # flag. Conservative default false; derived from Product rows below.
        "products": False,
        # C-cross Chunk 3 — derived capability. True when an admin has
        # configured a nutrition source (reserved seam — the integration
        # itself ships later). The per-user Settings page gates the
        # `complex` toggle on this flag; never leaks the source string.
        "nutrition_complex_available": False,
    }
    # AppSettings drives every install-wide flag at runtime. Wrapped so a
    # DB hiccup doesn't take the health probe down with it.
    try:
        from dora_api.features.app_settings.access import \
            get_or_create_app_setting
        from dora_api.persistence.sqlalchemy_repository import \
            SqlAlchemyRepository
        repo = SqlAlchemyRepository()
        setting = get_or_create_app_setting(repo)
        # FU-153 §7.1 — install-wide assistant gate is now just the
        # master kill-switch. Per-user enable + provider config layers on
        # top (see auth/update_me); useFeatureFlags wires the master flag
        # as the "feature is available here at all" signal.
        flags["assistant"] = bool(setting.master_llm_enabled)
        flags["scanning"] = bool(setting.scanning_enabled)
        flags["meal_planning"] = bool(setting.meal_planning_enabled)
        flags["money"] = bool(setting.money_enabled)
        flags["nutrition"] = bool(setting.nutrition_enabled)
        flags["companion_ingestion"] = bool(setting.companion_ingestion_enabled)
        flags["deals_email"] = bool(setting.deals_email_enabled)
        # FU-209 — products is on iff product data exists (data-presence gate),
        # not an AppSetting flag. R-003: one server-derived fact via /health.
        from dora_api.domain.entities.product import Product
        flags["products"] = repo.get(Product).count() > 0
        # C-cross Chunk 3 — derived from the seam value; never publish the
        # source string itself.
        flags["nutrition_complex_available"] = bool(
            (setting.nutrition_db_source or "").strip()
        )
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
