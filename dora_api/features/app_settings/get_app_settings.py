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
    llm_enabled: bool
    llm_base_url: str
    llm_model: str
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


def _to_dto(setting) -> AppSettingsDto:  # noqa: ANN001 — duck-typed AppSetting
    return AppSettingsDto(
        llm_enabled=bool(setting.llm_enabled),
        llm_base_url=setting.llm_base_url or "",
        llm_model=setting.llm_model or "",
        scanning_enabled=bool(setting.scanning_enabled),
        meal_planning_enabled=bool(setting.meal_planning_enabled),
        money_enabled=bool(setting.money_enabled),
        nutrition_enabled=bool(setting.nutrition_enabled),
        companion_ingestion_enabled=bool(setting.companion_ingestion_enabled),
        deals_email_enabled=bool(setting.deals_email_enabled),
        nutrition_db_source=setting.nutrition_db_source or "",
        timezone=setting.timezone or "UTC",
    )


@APP_SETTINGS_ROUTER.route("", methods=["GET"])
def get_app_settings():
    _Logger = logging.getLogger(__name__)
    _, err = _require_admin()
    if err is not None:
        return err
    setting = get_or_create_app_setting(SqlAlchemyRepository())
    _Logger.debug("Served app settings (llm_enabled=%s)", setting.llm_enabled)
    return ok(_to_dto(setting))
