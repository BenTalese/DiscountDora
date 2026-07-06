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
        # P8-05 — buy-verdict oracle. Defaults on (pure-personal
        # feature, no external calls); resolved from AppSetting below.
        "buy_verdict": True,
        "multi_user": True,     # register + admin role
        # FU-333 Bucket B — the install-wide `email` switch, and the two
        # `*_configured` R-014 signals (used by the SPA to reveal-and-disable
        # per-user channel toggles), now read through the operational-config
        # resolver so admin edits in Settings take effect without a restart.
        # Set conservatively here; resolved in the try block below alongside
        # the other AppSetting-driven flags.
        "email": False,
        "email_smtp_configured": False,
        "push_vapid_configured": False,
        "_push_vapid_private_present": bool(
            os.environ.get("DORA_VAPID_PRIVATE_KEY", "").strip()
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
        flags["buy_verdict"] = bool(getattr(setting, "buy_verdict_enabled", True))
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
        # FU-333 Bucket B — email + push R-014 signals now derive from the
        # operational-config resolver (AppSetting first, env fallback).
        from dora_api.features.app_settings.operational_config import \
            resolved_operational_config
        op_config = resolved_operational_config()
        flags["email"] = bool(op_config.email_enabled)
        flags["email_smtp_configured"] = bool(op_config.smtp_username)
        flags["push_vapid_configured"] = bool(
            op_config.vapid_public_key and flags["_push_vapid_private_present"]
        )
    except Exception:
        pass
    flags.pop("_push_vapid_private_present", None)
    return flags


def _locale_policy() -> dict[str, str]:
    """FU-043 (PROPOSAL_LOCALE_I18N Layer A) — install-wide currency + display
    locale, surfaced here (not on `/app-settings`) because every logged-in
    user's browser needs to render money in the household's chosen currency
    on boot, not just admins. Client wraps these in one
    `Intl.NumberFormat(locale, {style:'currency', currency})` and every
    money render routes through it (R-003). Wrapped in a try so a DB
    hiccup doesn't take the probe down — falls back to Dora's AU shipping
    defaults."""
    currency = "AUD"
    locale = "en-AU"
    try:
        from dora_api.features.app_settings.access import \
            get_or_create_app_setting
        from dora_api.persistence.sqlalchemy_repository import \
            SqlAlchemyRepository
        setting = get_or_create_app_setting(SqlAlchemyRepository())
        currency = (getattr(setting, "currency", None) or currency).strip() or currency
        locale = (getattr(setting, "locale", None) or locale).strip() or locale
    except Exception:
        pass
    return {"currency": currency, "locale": locale}


def _image_policy() -> dict[str, int]:
    """FU-345 — install-wide image compression knobs. Read on boot by
    the client-side `processImageFile` helper so every upload site
    (stock items, recipes, products, avatars, receipts, store logos)
    lands compressed to the admin's chosen quality + max dimension.
    Surfaced here (not on `/app-settings`) because it's a public
    policy every logged-in user's browser needs to apply, not admin-
    only configuration; the admin edit path is still the same
    admin-gated PATCH /app-settings. Wrapped in a try so a DB hiccup
    doesn't take the health probe down."""
    quality = 85
    max_dim = 1920
    try:
        from dora_api.features.app_settings.access import \
            get_or_create_app_setting
        from dora_api.persistence.sqlalchemy_repository import \
            SqlAlchemyRepository
        setting = get_or_create_app_setting(SqlAlchemyRepository())
        quality = int(getattr(setting, "image_quality", quality) or quality)
        max_dim = int(getattr(setting, "image_max_dimension", max_dim) or max_dim)
    except Exception:
        pass
    return {"quality": quality, "max_dimension": max_dim}


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
        "image_policy": _image_policy(),
        "locale_policy": _locale_policy(),
    }), 200
