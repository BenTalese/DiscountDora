"""GET /api/app-settings — install-wide settings for the admin Settings UI.

Admin-only. The assistant reads these values server-side (see access.py); this
endpoint exists so the admin page can show and edit them.
"""
import logging
from dataclasses import dataclass

from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.routers import APP_SETTINGS_ROUTER
from dora_api.features.users.update_user_as_admin import _require_admin
from dora_api.infrastructure.api_response import ok
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class AppSettingsDto:
    # install-wide master kill-switch (replaces the
    # per-install LLM URL/model/enabled config, which moved to User).
    master_llm_enabled: bool
    scanning_enabled: bool
    # buy-verdict oracle toggle.
    buy_verdict_enabled: bool
    # C-cross Chunk 1 — install-wide feature flags (proposal §2.6).
    meal_planning_enabled: bool
    money_enabled: bool
    nutrition_enabled: bool
    companion_ingestion_enabled: bool
    deals_email_enabled: bool
    # C-cross Chunk 3 — reserved seam for nutrition complex-mode. Empty
    # string ⇒ no source configured ⇒ users can't pick `complex`.
    nutrition_db_source: str
    # Meal Plans C-2.K — household IANA timezone for the "today" boundary.
    timezone: str
    # Alerts C-9.2 — household-wide expiring-soon window (PROPOSAL_ALERTS §3.3).
    expiring_soon_window_days: int
    # Phase D / FU-186 — admin-set URL the Product Search nav opens.
    product_search_url: str
    # AU vs US per-unit display locale.
    unit_pricing_locale: str
    # install-wide currency (ISO 4217) + display locale (BCP-47).
    # Layer A of PROPOSAL_LOCALE_I18N; also mirrored on /api/health so
    # every client session (not just admin) reads them.
    currency: str
    locale: str
    # backup library controls. See AppSetting entity.
    backup_retention_count: int
    backup_storage_path: str
    # image compression knobs. See AppSetting entity.
    image_quality: int
    image_max_dimension: int
    # PROPOSAL_STOCKTAKE_MODE §4 + §8 — global cadence band + Auto toggle.
    stocktake_default_cadence_band: str
    stocktake_auto_tuning_enabled: bool
    # operational config (was `DORA_*` env vars).
    # Bucket-C secrets (SMTP password, VAPID private key) are stored
    # encrypted-at-rest on the row; the DTO exposes a `<field>_configured`
    # bool instead of the ciphertext so the admin UI can show Set / Change
    # / Clear without ever transporting the secret.
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password_configured: bool
    smtp_from: str
    smtp_use_tls: bool
    vapid_public_key: str
    vapid_private_key_configured: bool
    vapid_subject: str
    piper_bin: str
    piper_bundled_voice_dir: str
    piper_voice: str
    email_enabled: bool
    audit_retention_days: int
    public_url: str


def _to_dto(setting) -> AppSettingsDto:  # noqa: ANN001 — duck-typed AppSetting
    return AppSettingsDto(
        master_llm_enabled=bool(setting.master_llm_enabled),
        scanning_enabled=bool(setting.scanning_enabled),
        buy_verdict_enabled=bool(getattr(setting, "buy_verdict_enabled", True)),
        meal_planning_enabled=bool(setting.meal_planning_enabled),
        money_enabled=bool(setting.money_enabled),
        nutrition_enabled=bool(setting.nutrition_enabled),
        companion_ingestion_enabled=bool(setting.companion_ingestion_enabled),
        deals_email_enabled=bool(setting.deals_email_enabled),
        nutrition_db_source=setting.nutrition_db_source or "",
        timezone=setting.timezone or "UTC",
        expiring_soon_window_days=int(setting.expiring_soon_window_days),
        product_search_url=setting.product_search_url or "",
        unit_pricing_locale=getattr(setting, "unit_pricing_locale", None) or "AU",
        currency=getattr(setting, "currency", None) or "AUD",
        locale=getattr(setting, "locale", None) or "en-AU",
        backup_retention_count=int(getattr(setting, "backup_retention_count", 5) or 5),
        backup_storage_path=getattr(setting, "backup_storage_path", None) or "",
        image_quality=int(getattr(setting, "image_quality", 85) or 85),
        image_max_dimension=int(getattr(setting, "image_max_dimension", 1920) or 1920),
        stocktake_default_cadence_band=(
            getattr(setting, "stocktake_default_cadence_band", None) or "fortnightly"
        ),
        stocktake_auto_tuning_enabled=bool(
            getattr(setting, "stocktake_auto_tuning_enabled", True)
        ),
        smtp_host=getattr(setting, "smtp_host", None) or "",
        smtp_port=int(getattr(setting, "smtp_port", 587) or 587),
        smtp_username=getattr(setting, "smtp_username", None) or "",
        smtp_password_configured=bool((getattr(setting, "smtp_password_encrypted", None) or "").strip()),
        smtp_from=getattr(setting, "smtp_from", None) or "",
        smtp_use_tls=bool(getattr(setting, "smtp_use_tls", True)),
        vapid_public_key=getattr(setting, "vapid_public_key", None) or "",
        vapid_private_key_configured=bool((getattr(setting, "vapid_private_key_encrypted", None) or "").strip()),
        vapid_subject=getattr(setting, "vapid_subject", None) or "mailto:admin@dora.local",
        piper_bin=getattr(setting, "piper_bin", None) or "",
        piper_bundled_voice_dir=getattr(setting, "piper_bundled_voice_dir", None) or "",
        piper_voice=getattr(setting, "piper_voice", None) or "",
        email_enabled=bool(getattr(setting, "email_enabled", False)),
        audit_retention_days=int(getattr(setting, "audit_retention_days", 365) or 365),
        public_url=getattr(setting, "public_url", None) or "",
    )


@APP_SETTINGS_ROUTER.route("", methods=["GET"])
def get_app_settings():
    _Logger = logging.getLogger(__name__)
    _, err = _require_admin()
    if err is not None:
        return err
    setting = get_or_create_app_setting(SqlAlchemyRepository())
    _Logger.debug("Served app settings (master_llm_enabled=%s)", setting.master_llm_enabled)
    return ok(_to_dto(setting))
