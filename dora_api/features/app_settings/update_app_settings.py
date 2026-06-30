"""PATCH /api/app-settings — admin-only edit of install-wide settings.

Only the assistant (BYO-LLM) config lives here for now. Fields are optional;
only those present in the request body are changed.
"""
import logging
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.app_settings.clock import is_valid_timezone
from dora_api.features.app_settings.get_app_settings import AppSettingsDto, _to_dto
from dora_api.features.routers import APP_SETTINGS_ROUTER
from dora_api.features.users.update_user_as_admin import _require_admin
from dora_api.infrastructure.api_response import bad_request, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateAppSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # FU-153 §7.1 — single install-wide master kill-switch for the
    # assistant feature. Per-user LLM URL/model/provider/API key live on
    # the User row now (see auth/update_me).
    master_llm_enabled: bool | None = None
    scanning_enabled: bool | None = None
    # C-cross Chunk 1 — install-wide feature flags (proposal §2.6).
    meal_planning_enabled: bool | None = None
    money_enabled: bool | None = None
    nutrition_enabled: bool | None = None
    companion_ingestion_enabled: bool | None = None
    deals_email_enabled: bool | None = None
    # C-cross Chunk 3 — reserved seam for nutrition complex-mode. Empty
    # string is allowed (and is the default-seam state); the actual
    # source schema lands when the complex-mode integration ships.
    nutrition_db_source: str | None = Field(default=None, max_length=255)
    # Meal Plans C-2.K — household IANA timezone (validated below).
    timezone: str | None = Field(default=None, max_length=64)
    # Alerts C-9.2 — household-wide alert thresholds (bounds double as R-010
    # validation: the window is 1–365 days; the stocktake default 0–3650).
    expiring_soon_window_days: int | None = Field(default=None, ge=1, le=365)
    default_days_until_stocktake_alert: int | None = Field(default=None, ge=0, le=3650)
    # Phase D / FU-186 — admin-set URL the Product Search nav opens.
    # Empty string ⇒ unset; the nav entry renders disabled with a hint.
    # We allow any http(s) URL or empty; deeper validation is the operator's
    # problem (the field never echoes back as a clickable link to other
    # users — it ALWAYS opens via target="_blank" rel="noopener").
    product_search_url: str | None = Field(default=None, max_length=500)
    # FU-227 follow-up — AU vs US per-unit display locale.
    unit_pricing_locale: str | None = Field(default=None, max_length=8)


@dataclass(slots=True)
class UpdateAppSettingsResponse:
    invalid_reason: str | None = None
    dto: AppSettingsDto | None = None


class UpdateAppSettingsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateAppSettingsRequest) -> UpdateAppSettingsResponse:
        setting = get_or_create_app_setting(self.repository)
        set_fields = request.model_fields_set

        if "master_llm_enabled" in set_fields and request.master_llm_enabled is not None:
            setting.master_llm_enabled = request.master_llm_enabled
        if "scanning_enabled" in set_fields and request.scanning_enabled is not None:
            setting.scanning_enabled = request.scanning_enabled
        # C-cross Chunk 1 — install feature flags. Partial-update semantics
        # like every other field above: only fields present in the body
        # change; the rest are left alone.
        for _Attr in (
            "meal_planning_enabled",
            "money_enabled",
            "nutrition_enabled",
            "companion_ingestion_enabled",
            "deals_email_enabled",
        ):
            if _Attr in set_fields:
                value = getattr(request, _Attr)
                if value is not None:
                    setattr(setting, _Attr, value)
        # C-cross Chunk 3 — nutrition source seam. Free-form for now;
        # later complex-mode work parses it. Strip on save.
        if "nutrition_db_source" in set_fields:
            setting.nutrition_db_source = (request.nutrition_db_source or "").strip()

        # Meal Plans C-2.K — household timezone. Validate against the IANA
        # database so an unparseable zone can't silently degrade the "today"
        # boundary to UTC for the whole install.
        if "timezone" in set_fields and request.timezone is not None:
            _Tz = request.timezone.strip()
            if not is_valid_timezone(_Tz):
                return UpdateAppSettingsResponse(
                    invalid_reason=f"'{_Tz}' is not a recognised IANA timezone."
                )
            setting.timezone = _Tz

        # Alerts C-9.2 — household-wide alert thresholds. Bounds enforced by
        # the request model above (R-010).
        if "expiring_soon_window_days" in set_fields and request.expiring_soon_window_days is not None:
            setting.expiring_soon_window_days = request.expiring_soon_window_days
        if (
            "default_days_until_stocktake_alert" in set_fields
            and request.default_days_until_stocktake_alert is not None
        ):
            setting.default_days_until_stocktake_alert = request.default_days_until_stocktake_alert

        # FU-227 follow-up — unit_pricing_locale. Validated against the
        # supported set so a typo can't silently degrade display.
        if "unit_pricing_locale" in set_fields and request.unit_pricing_locale is not None:
            from dora_api.domain.units import SUPPORTED_PRICING_LOCALES
            _Locale = request.unit_pricing_locale.strip().upper()
            if _Locale not in SUPPORTED_PRICING_LOCALES:
                return UpdateAppSettingsResponse(
                    invalid_reason=(
                        f"'{_Locale}' is not a supported unit-pricing locale. "
                        f"Supported: {sorted(SUPPORTED_PRICING_LOCALES)}."
                    ),
                )
            setting.unit_pricing_locale = _Locale

        # Phase D / FU-186 — product_search_url. Strip; reject obviously
        # non-http schemes so a typo doesn't render a hostile link, but
        # otherwise leave validation to the operator.
        if "product_search_url" in set_fields:
            _Url = (request.product_search_url or "").strip()
            if _Url and not (_Url.startswith("http://") or _Url.startswith("https://")):
                return UpdateAppSettingsResponse(
                    invalid_reason="Product search URL must start with http:// or https://."
                )
            setting.product_search_url = _Url

        # FU-153 §7.1 — the install-wide setting is now a master kill-
        # switch only; the per-user "have you finished setting up?"
        # validation moved to auth/update_me.py.

        self.repository.save_changes()
        return UpdateAppSettingsResponse(dto=_to_dto(setting))


@APP_SETTINGS_ROUTER.route("", methods=["PATCH"])
@has_request_body(UpdateAppSettingsRequest)
def update_app_settings():
    _Logger = logging.getLogger(__name__)
    _, err = _require_admin()
    if err is not None:
        return err
    _Request: UpdateAppSettingsRequest = get_request_body()
    _Response = UpdateAppSettingsHandler().handle(_Request)
    if _Response.invalid_reason is not None:
        return bad_request("Invalid settings.", detail=_Response.invalid_reason)
    _Logger.info("Admin updated app settings (master_llm_enabled=%s)", _Response.dto.master_llm_enabled)
    return ok(_Response.dto)
