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
    # FU-153 §7.1 — install-wide master kill-switch (replaces the
    # per-install LLM URL/model/enabled config, which moved to User).
    master_llm_enabled: bool
    scanning_enabled: bool
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
    # Alerts C-9.2 — household-wide alert thresholds (PROPOSAL_ALERTS §3.3).
    expiring_soon_window_days: int
    default_days_until_stocktake_alert: int
    # Phase D / FU-186 — admin-set URL the Product Search nav opens.
    product_search_url: str
    # FU-227 follow-up — AU vs US per-unit display locale.
    unit_pricing_locale: str
    # FU-342 — backup library controls. See AppSetting entity.
    backup_retention_count: int
    backup_storage_path: str
    # FU-345 — image compression knobs. See AppSetting entity.
    image_quality: int
    image_max_dimension: int


def _to_dto(setting) -> AppSettingsDto:  # noqa: ANN001 — duck-typed AppSetting
    return AppSettingsDto(
        master_llm_enabled=bool(setting.master_llm_enabled),
        scanning_enabled=bool(setting.scanning_enabled),
        meal_planning_enabled=bool(setting.meal_planning_enabled),
        money_enabled=bool(setting.money_enabled),
        nutrition_enabled=bool(setting.nutrition_enabled),
        companion_ingestion_enabled=bool(setting.companion_ingestion_enabled),
        deals_email_enabled=bool(setting.deals_email_enabled),
        nutrition_db_source=setting.nutrition_db_source or "",
        timezone=setting.timezone or "UTC",
        expiring_soon_window_days=int(setting.expiring_soon_window_days),
        default_days_until_stocktake_alert=int(setting.default_days_until_stocktake_alert),
        product_search_url=setting.product_search_url or "",
        unit_pricing_locale=getattr(setting, "unit_pricing_locale", None) or "AU",
        backup_retention_count=int(getattr(setting, "backup_retention_count", 5) or 5),
        backup_storage_path=getattr(setting, "backup_storage_path", None) or "",
        image_quality=int(getattr(setting, "image_quality", 85) or 85),
        image_max_dimension=int(getattr(setting, "image_max_dimension", 1920) or 1920),
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
